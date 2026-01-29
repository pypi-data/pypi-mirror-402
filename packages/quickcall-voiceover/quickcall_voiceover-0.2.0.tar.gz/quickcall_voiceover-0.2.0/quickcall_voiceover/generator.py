"""Voice-over generation with pluggable TTS backends."""

from __future__ import annotations

import json
import wave
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rich.console import Console

from quickcall_voiceover.backends import TTSBackend, get_backend


def load_config(config_path: Path) -> dict:
    """Load configuration from JSON file."""
    with open(config_path, "r") as f:
        return json.load(f)


def combine_wav_files(
    wav_files: list[Path], output_path: Path, console: Console | None = None
) -> bool:
    """Combine multiple WAV files into a single file."""
    if not wav_files:
        return False

    try:
        # Read first file to get parameters
        with wave.open(str(wav_files[0]), "rb") as first:
            params = first.getparams()

        # Combine all files
        with wave.open(str(output_path), "wb") as output:
            output.setparams(params)
            for wav_file in wav_files:
                with wave.open(str(wav_file), "rb") as w:
                    output.writeframes(w.readframes(w.getnframes()))

        return True
    except Exception as e:
        msg = f"Error combining WAV files: {e}"
        if console:
            console.print(f"[red]{msg}[/red]")
        else:
            print(msg)
        return False


def generate_from_text(
    lines: list[str],
    voice: str | None = None,
    output_dir: Path | None = None,
    models_dir: Path | None = None,
    combine: bool = False,
    combined_filename: str = "combined_voiceover.wav",
    console: Console | None = None,
    backend: str = "piper",
    # Piper-specific params (for backward compatibility)
    length_scale: float | None = None,
    noise_scale: float | None = None,
    noise_w: float | None = None,
    sentence_silence: float | None = None,
    # Kokoro-specific params
    speed: float | None = None,
) -> bool:
    """
    Generate voice-over audio from a list of text lines.

    Args:
        lines: List of text strings, each becomes a segment
        voice: Voice model name (default depends on backend)
        output_dir: Directory for output files (default: ./output)
        models_dir: Directory for voice models (default: ./models)
        combine: If True, also create a single combined audio file
        combined_filename: Name for the combined output file
        console: Rich console for styled output
        backend: TTS backend to use ("piper" or "kokoro")
        length_scale: [Piper] Speech speed (lower = faster), default 1.0
        noise_scale: [Piper] Voice variation, default 0.667
        noise_w: [Piper] Phoneme width noise, default 0.8
        sentence_silence: [Piper] Silence between sentences, default 0.5
        speed: [Kokoro] Speech speed multiplier, default 1.0

    Returns:
        True if all segments generated successfully
    """
    # Setup directories
    if output_dir is None:
        output_dir = Path.cwd() / "output"
    if models_dir is None:
        models_dir = Path.cwd() / "models"

    output_dir = Path(output_dir)
    models_dir = Path(models_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get backend class and create instance
    BackendClass = get_backend(backend)

    # Use default voice if not specified
    if voice is None:
        voice = BackendClass.default_voice()

    # Build backend kwargs based on type
    backend_kwargs: dict = {
        "voice": voice,
        "models_dir": models_dir,
        "console": console,
    }

    if backend == "piper":
        if length_scale is not None:
            backend_kwargs["length_scale"] = length_scale
        if noise_scale is not None:
            backend_kwargs["noise_scale"] = noise_scale
        if noise_w is not None:
            backend_kwargs["noise_w"] = noise_w
        if sentence_silence is not None:
            backend_kwargs["sentence_silence"] = sentence_silence
    elif backend == "kokoro":
        if speed is not None:
            backend_kwargs["speed"] = speed

    tts: TTSBackend = BackendClass(**backend_kwargs)
    tts.setup()

    if console:
        console.print(f"\n[bold]Generating {len(lines)} segments...[/bold]\n")

    # Generate each segment
    success_count = 0
    generated_files: list[Path] = []

    for i, text in enumerate(lines, 1):
        segment_id = f"segment_{i:03d}"
        output_file = output_dir / f"{segment_id}.wav"

        display_text = text[:40] + "..." if len(text) > 40 else text
        if console:
            console.print(f"  [{i}/{len(lines)}] {display_text}")

        success = tts.generate(text=text, output_path=output_file)

        if success:
            if console:
                console.print(f"       [green]✓[/green] {output_file.name}")
            success_count += 1
            generated_files.append(output_file)
        else:
            if console:
                console.print("       [red]✗ FAILED[/red]")

    if console:
        console.print(f"\n[bold]Completed:[/bold] {success_count}/{len(lines)} segments")

    # Combine files if requested
    if combine and generated_files:
        combined_path = output_dir / combined_filename
        if console:
            console.print(f"\n[yellow]⊕[/yellow] Combining into: [cyan]{combined_path}[/cyan]")

        if combine_wav_files(generated_files, combined_path, console):
            if console:
                console.print("[green]✓[/green] Combined file saved")
        else:
            if console:
                console.print("[red]✗ Failed to create combined file[/red]")

    return success_count == len(lines)


def generate_voiceover(
    config_path: Path,
    output_dir: Path | None = None,
    models_dir: Path | None = None,
    combine: bool = False,
    combined_filename: str = "combined_voiceover.wav",
    console: Console | None = None,
    backend: str | None = None,
    voice: str | None = None,
) -> bool:
    """
    Generate voice-over audio from a config file.

    Args:
        config_path: Path to the JSON configuration file
        output_dir: Directory for output files (default: ./output)
        models_dir: Directory for voice models (default: ./models)
        combine: If True, also create a single combined audio file
        combined_filename: Name for the combined output file
        console: Rich console for styled output
        backend: TTS backend to use (default: from config or "piper")
        voice: Voice to use (overrides config)

    Returns:
        True if all segments generated successfully
    """
    config_path = Path(config_path)

    # Setup directories
    if output_dir is None:
        output_dir = Path.cwd() / "output"
    if models_dir is None:
        models_dir = Path.cwd() / "models"

    output_dir = Path(output_dir)
    models_dir = Path(models_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load config
    if console:
        console.print(f"[dim]Loading config: {config_path}[/dim]")
    config = load_config(config_path)

    # Voice settings
    voice_config = config.get("voice", {})
    output_format = config.get("output", {}).get("format", "wav")

    # Determine backend from config or parameter
    backend_name = backend or voice_config.get("backend", "piper")
    BackendClass = get_backend(backend_name)

    # Use voice override, or from config, or default for backend
    voice_name = voice or voice_config.get("model") or BackendClass.default_voice()

    # Build backend kwargs
    backend_kwargs: dict = {
        "voice": voice_name,
        "models_dir": models_dir,
        "console": console,
    }

    # Add backend-specific params from config
    if backend_name == "piper":
        for key in ["length_scale", "noise_scale", "noise_w", "sentence_silence"]:
            if key in voice_config:
                backend_kwargs[key] = voice_config[key]
    elif backend_name == "kokoro":
        if "speed" in voice_config:
            backend_kwargs["speed"] = voice_config["speed"]
        if "lang_code" in voice_config:
            backend_kwargs["lang_code"] = voice_config["lang_code"]

    tts: TTSBackend = BackendClass(**backend_kwargs)
    tts.setup()

    segments = config.get("segments", [])

    if console:
        console.print(f"[dim]Backend: {backend_name} | Voice: {voice_name}[/dim]")
        console.print(f"[dim]Output: {output_dir}[/dim]")
        console.print(f"\n[bold]Generating {len(segments)} segments...[/bold]\n")
    else:
        print(f"Backend: {backend_name}")
        print(f"Voice: {voice_name}")
        print(f"Output directory: {output_dir}")
        print(f"Total segments: {len(segments)}")
        print("-" * 50)

    # Generate each segment
    success_count = 0
    generated_files: list[Path] = []

    for i, segment in enumerate(segments, 1):
        segment_id = segment.get("id", f"segment_{i:03d}")
        text = segment.get("text", "")
        output_file = output_dir / f"{segment_id}.{output_format}"

        display_text = text[:40] + "..." if len(text) > 40 else text

        if console:
            console.print(f"  [{i}/{len(segments)}] [cyan]{segment_id}[/cyan]")
            console.print(f"       {display_text}")
        else:
            print(f"Generating: {segment_id}")
            print(f"  Text: {display_text}")

        success = tts.generate(text=text, output_path=output_file)

        if success:
            if console:
                console.print(f"       [green]✓[/green] {output_file.name}")
            else:
                print(f"  Saved: {output_file}")
            success_count += 1
            generated_files.append(output_file)
        else:
            if console:
                console.print("       [red]✗ FAILED[/red]")
            else:
                print("  FAILED!")

    if console:
        console.print(f"\n[bold]Completed:[/bold] {success_count}/{len(segments)} segments")
    else:
        print("-" * 50)
        print(f"Completed: {success_count}/{len(segments)} segments")

    # Combine files if requested
    if combine and generated_files:
        combined_path = output_dir / combined_filename

        if console:
            console.print(f"\n[yellow]⊕[/yellow] Combining into: [cyan]{combined_path}[/cyan]")
        else:
            print("-" * 50)
            print(f"Combining {len(generated_files)} files into: {combined_path}")

        if combine_wav_files(generated_files, combined_path, console):
            if console:
                console.print("[green]✓[/green] Combined file saved")
            else:
                print(f"Combined file saved: {combined_path}")
        else:
            if console:
                console.print("[red]✗ Failed to create combined file[/red]")
            else:
                print("Failed to create combined file")

    all_success = success_count == len(segments)
    if not console:
        if all_success:
            print("All voice-over segments generated successfully!")
        else:
            print("Some segments failed. Check errors above.")

    return all_success
