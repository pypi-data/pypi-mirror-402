"""Command-line interface for QuickCall VoiceOver."""

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from quickcall_voiceover.backends import BACKENDS, get_backend
from quickcall_voiceover.generator import generate_from_text, generate_voiceover

console = Console()

DEFAULT_BACKEND = "piper"


def show_banner() -> None:
    """Display the CLI banner."""
    console.print()
    console.print(
        Panel(
            "[bold cyan]QuickCall VoiceOver[/bold cyan]\n"
            "[dim]Multi-backend TTS: Piper | Kokoro[/dim]",
            border_style="cyan",
            padding=(0, 2),
        )
    )
    console.print()


def show_voice_table(backend_name: str = "piper") -> None:
    """Display available voices for a backend."""
    try:
        BackendClass = get_backend(backend_name)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        return

    voices = BackendClass.list_voices()
    default_voice = BackendClass.default_voice()

    table = Table(
        title=f"Available Voices ({backend_name.capitalize()})",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("#", style="dim", width=3)
    table.add_column("Voice ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Description", style="white")

    for i, (voice_id, (name, desc)) in enumerate(voices.items(), 1):
        default_mark = " [yellow](default)[/yellow]" if voice_id == default_voice else ""
        table.add_row(str(i), voice_id, name + default_mark, desc)

    console.print(table)
    console.print()

    if backend_name == "piper":
        console.print(
            "[dim]Browse all Piper voices: https://rhasspy.github.io/piper-samples/[/dim]"
        )
    elif backend_name == "kokoro":
        console.print("[dim]Kokoro info: https://huggingface.co/hexgrad/Kokoro-82M[/dim]")
    console.print()


def show_all_backends() -> None:
    """Show available backends."""
    console.print("\n[bold]Available TTS Backends:[/bold]\n")
    for name in BACKENDS:
        BackendClass = BACKENDS[name]
        console.print(f"  [cyan]{name}[/cyan] - {len(BackendClass.list_voices())} voices")
    console.print()


def select_voice(backend_name: str = "piper") -> str:
    """Interactive voice selection for a backend."""
    BackendClass = get_backend(backend_name)
    voices = BackendClass.list_voices()
    default_voice = BackendClass.default_voice()

    show_voice_table(backend_name)

    choice = Prompt.ask(
        "[bold]Select a voice[/bold]",
        choices=[str(i) for i in range(1, len(voices) + 1)] + ["custom"],
        default="1",
    )

    if choice == "custom":
        return Prompt.ask("[bold]Enter custom voice ID[/bold]", default=default_voice)

    voice_list = list(voices.keys())
    return voice_list[int(choice) - 1]


def file_text_mode(
    text_file: Path,
    output_dir: Path | None,
    combine: bool,
    combined_name: str,
    voice: str | None = None,
    config_path: Path | None = None,
    backend: str = "piper",
) -> int:
    """Generate voice-over from a text file, optionally with voice config from JSON."""
    import json

    show_banner()

    if not text_file.exists():
        console.print(f"[red]Error: Text file not found: {text_file}[/red]")
        return 1

    # Read lines from file
    lines = [line.strip() for line in text_file.read_text().splitlines() if line.strip()]

    if not lines:
        console.print("[red]No text found in file. Exiting.[/red]")
        return 1

    # Load voice settings from config if provided
    voice_settings = {}
    config_backend = None
    if config_path:
        if not config_path.exists():
            console.print(f"[red]Error: Config file not found: {config_path}[/red]")
            return 1
        try:
            config = json.loads(config_path.read_text())
            voice_settings = config.get("voice", {})
            config_backend = voice_settings.get("backend")
        except json.JSONDecodeError as e:
            console.print(f"[red]Error parsing config file: {e}[/red]")
            return 1

    # Determine backend (CLI arg > config > default)
    selected_backend = backend if backend != "piper" else (config_backend or backend)
    BackendClass = get_backend(selected_backend)

    # Use provided voice, or from config, or default for backend
    selected_voice = voice or voice_settings.get("model") or BackendClass.default_voice()

    config_info = f"\nConfig: [cyan]{config_path}[/cyan]" if config_path else ""

    console.print(
        Panel(
            f"[bold]File Mode[/bold]\n\n"
            f"Text: [cyan]{text_file}[/cyan]\n"
            f"Lines: [cyan]{len(lines)}[/cyan]\n"
            f"Backend: [cyan]{selected_backend}[/cyan]\n"
            f"Voice: [cyan]{selected_voice}[/cyan]{config_info}\n"
            f"Output: [cyan]{output_dir or './output'}[/cyan]\n"
            f"Combine: [cyan]{combine}[/cyan]",
            title="Settings",
            border_style="blue",
        )
    )
    console.print()

    # Build kwargs based on backend
    gen_kwargs: dict = {
        "lines": lines,
        "voice": selected_voice,
        "output_dir": output_dir or Path("./output"),
        "combine": combine,
        "combined_filename": combined_name,
        "console": console,
        "backend": selected_backend,
    }

    # Add backend-specific params from config
    if selected_backend == "piper":
        for key in ["length_scale", "noise_scale", "noise_w", "sentence_silence"]:
            if key in voice_settings:
                gen_kwargs[key] = voice_settings[key]
    elif selected_backend == "kokoro":
        if "speed" in voice_settings:
            gen_kwargs["speed"] = voice_settings["speed"]

    success = generate_from_text(**gen_kwargs)

    if success:
        console.print(
            Panel(
                "[bold green]✓ All segments generated successfully![/bold green]",
                border_style="green",
            )
        )
    else:
        console.print(Panel("[bold red]✗ Some segments failed[/bold red]", border_style="red"))

    return 0 if success else 1


def interactive_text_mode(backend: str = "piper") -> int:
    """Interactive text-based voice-over generation."""
    show_banner()

    console.print(
        Panel(
            f"[bold]Text Mode[/bold]\n\n"
            f"Backend: [cyan]{backend}[/cyan]\n"
            "Generate voice-over from text directly.\n"
            "Each line becomes a separate audio segment.",
            title="Mode",
            border_style="blue",
        )
    )
    console.print()

    # Select voice for the backend
    voice = select_voice(backend)
    console.print(f"\n[green]✓[/green] Selected voice: [cyan]{voice}[/cyan]\n")

    # Confirm before proceeding
    if not Confirm.ask(f"[bold]Use voice '[cyan]{voice}[/cyan]'?[/bold]", default=True):
        voice = select_voice(backend)

    # Get output settings
    output_dir = Path(Prompt.ask("[bold]Output directory[/bold]", default="./output"))
    combine = Confirm.ask("[bold]Combine all segments into one file?[/bold]", default=False)

    # Get text input
    console.print("\n[bold]Enter your text[/bold] (one segment per line, empty line to finish):\n")

    lines = []
    while True:
        try:
            line = input()
            if not line:
                break
            lines.append(line)
        except EOFError:
            break

    if not lines:
        console.print("[red]No text provided. Exiting.[/red]")
        return 1

    console.print(f"\n[green]✓[/green] Got {len(lines)} segments\n")

    # Generate
    with console.status("[bold green]Generating voice-over..."):
        success = generate_from_text(
            lines=lines,
            voice=voice,
            output_dir=output_dir,
            combine=combine,
            console=console,
            backend=backend,
        )

    if success:
        console.print(
            Panel(
                "[bold green]✓ All segments generated successfully![/bold green]",
                border_style="green",
            )
        )
    else:
        console.print(Panel("[bold red]✗ Some segments failed[/bold red]", border_style="red"))

    return 0 if success else 1


def config_mode(args: argparse.Namespace) -> int:
    """Config file based generation."""
    show_banner()

    backend_info = f"\nBackend: [cyan]{args.backend}[/cyan]" if args.backend else ""
    voice_info = f"\nVoice: [cyan]{args.voice}[/cyan]" if args.voice else ""

    console.print(
        Panel(
            f"[bold]Config Mode[/bold]\n\n"
            f"Config: [cyan]{args.config}[/cyan]{backend_info}{voice_info}\n"
            f"Output: [cyan]{args.output or './output'}[/cyan]\n"
            f"Combine: [cyan]{args.combine}[/cyan]",
            title="Settings",
            border_style="blue",
        )
    )
    console.print()

    if not args.config.exists():
        console.print(f"[red]Error: Config file not found: {args.config}[/red]")
        return 1

    success = generate_voiceover(
        config_path=args.config,
        output_dir=args.output,
        models_dir=args.models,
        combine=args.combine,
        combined_filename=args.combined_name,
        console=console,
        backend=args.backend,
        voice=args.voice,
    )

    if success:
        console.print(
            Panel(
                "[bold green]✓ All segments generated successfully![/bold green]",
                border_style="green",
            )
        )
    else:
        console.print(Panel("[bold red]✗ Some segments failed[/bold red]", border_style="red"))

    return 0 if success else 1


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="quickcall-voiceover",
        description="Generate voice-over audio using multiple TTS backends (Piper, Kokoro)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Piper (default)
  quickcall-voiceover config.json                    Generate from config file
  quickcall-voiceover config.json --combine          Generate and combine into one file
  quickcall-voiceover -t script.txt -c               Generate from text file and combine

  # Kokoro
  quickcall-voiceover -b kokoro -t script.txt -c     Use Kokoro backend
  quickcall-voiceover -b kokoro --voices             Show Kokoro voices

  # Voice selection
  quickcall-voiceover -t script.txt -v en_US-ryan-high     Piper voice
  quickcall-voiceover -b kokoro -t script.txt -v af_heart  Kokoro voice

  # Interactive mode
  quickcall-voiceover --text                         Interactive text mode
  quickcall-voiceover -b kokoro --text               Interactive with Kokoro

  # Show voices
  quickcall-voiceover --voices                       Show Piper voices
  quickcall-voiceover -b kokoro --voices             Show Kokoro voices
        """,
    )
    parser.add_argument(
        "config",
        type=Path,
        nargs="?",
        help="Path to the JSON configuration file",
    )
    parser.add_argument(
        "-b",
        "--backend",
        type=str,
        choices=list(BACKENDS.keys()),
        default=None,
        help="TTS backend to use (default: piper, or from config)",
    )
    parser.add_argument(
        "-t",
        "--text",
        type=Path,
        nargs="?",
        const=True,
        default=None,
        help="Text mode: provide a .txt file path, or use without argument for interactive input",
    )
    parser.add_argument(
        "-v",
        "--voice",
        type=str,
        default=None,
        help="Voice to use (default depends on backend)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output directory for generated audio files (default: ./output)",
    )
    parser.add_argument(
        "-m",
        "--models",
        type=Path,
        default=None,
        help="Directory for voice models (default: ./models)",
    )
    parser.add_argument(
        "-c",
        "--combine",
        action="store_true",
        help="Also create a single combined audio file from all segments",
    )
    parser.add_argument(
        "--combined-name",
        type=str,
        default="combined_voiceover.wav",
        help="Filename for the combined output (default: combined_voiceover.wav)",
    )
    parser.add_argument(
        "--voices",
        action="store_true",
        help="Show available voice models and exit",
    )

    args = parser.parse_args()

    # Determine effective backend
    effective_backend = args.backend or DEFAULT_BACKEND

    # Show voices and exit
    if args.voices:
        show_banner()
        show_voice_table(effective_backend)
        show_all_backends()
        return 0

    # Text mode - file or interactive
    if args.text is not None:
        if args.text is True:
            # Interactive mode (no file provided)
            return interactive_text_mode(effective_backend)
        else:
            # File mode
            return file_text_mode(
                text_file=args.text,
                output_dir=args.output,
                combine=args.combine,
                combined_name=args.combined_name,
                voice=args.voice,
                config_path=args.config,
                backend=effective_backend,
            )

    # Config mode requires a config file
    if not args.config:
        parser.print_help()
        console.print("\n[yellow]Tip: Use --text for interactive text mode[/yellow]")
        console.print("[yellow]     Use -b kokoro to switch to Kokoro backend[/yellow]")
        return 1

    return config_mode(args)


if __name__ == "__main__":
    sys.exit(main())
