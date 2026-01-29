<p align="center">
  <img src="https://quickcall.dev/assets/v1/qc-full-512px-white.png" alt="QuickCall" width="400">
</p>

<h3 align="center">QuickCall VoiceOver</h3>

<p align="center">
  <em>Multi-backend TTS tool for creating voice-over audio assets</em>
</p>

<p align="center">
  <a href="https://pypi.org/project/quickcall-voiceover/"><img src="https://img.shields.io/pypi/v/quickcall-voiceover?color=blue" alt="PyPI"></a>
  <a href="https://github.com/quickcall-dev/quickcall-voiceover/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-Apache%202.0-green" alt="License"></a>
  <a href="https://quickcall.dev"><img src="https://img.shields.io/badge/Web-quickcall.dev-000000?logo=googlechrome&logoColor=white" alt="Web"></a>
  <a href="https://discord.gg/DtnMxuE35v"><img src="https://img.shields.io/badge/Discord-Join%20Us-5865F2?logo=discord&logoColor=white" alt="Discord"></a>
</p>

<p align="center">
  <a href="#install">Install</a> |
  <a href="#quick-start">Quick Start</a> |
  <a href="#backends">Backends</a> |
  <a href="#cli-options">CLI Options</a> |
  <a href="#voice-models">Voice Models</a> |
  <a href="#configuration">Configuration</a> |
  <a href="#docker">Docker</a> |
  <a href="#license">License</a>
</p>

---

## Install

### Install with Piper backend

```bash
uv pip install quickcall-voiceover[piper]
```

### Install with Kokoro backend

```bash
uv pip install quickcall-voiceover[kokoro]

# macOS: Also install espeak-ng
brew install espeak-ng
```

### Install with all backends

```bash
uv pip install quickcall-voiceover[all]

# macOS: Also install espeak-ng for Kokoro
brew install espeak-ng
```

## Quick Start

### Config Mode

```bash
# Piper (default)
quickcall-voiceover config.json --combine

# Kokoro
quickcall-voiceover -b kokoro -v af_heart config.json --combine
```

### Text File Mode

```bash
# Piper
quickcall-voiceover -t script.txt -c -o ./output

# Kokoro with af_heart voice
quickcall-voiceover -b kokoro -v af_heart -t script.txt -c -o ./output
```

### Interactive Mode

```bash
quickcall-voiceover --text
quickcall-voiceover -b kokoro --text
```

### Show Available Voices

```bash
quickcall-voiceover --voices           # Piper voices
quickcall-voiceover -b kokoro --voices # Kokoro voices
```

## Backends

| Backend | Model | Quality | Speed | Install |
|---------|-------|---------|-------|---------|
| **Piper** | Various | Medium-High | Fast | Default |
| **Kokoro** | Kokoro-82M | High | Medium | `[kokoro]` extra |

## CLI Options

```
quickcall-voiceover [CONFIG] [OPTIONS]

Arguments:
  CONFIG                Path to JSON configuration file

Options:
  -b, --backend         TTS backend: piper, kokoro (default: piper)
  -t, --text [FILE]     Text mode: provide .txt file or use interactively
  -v, --voice VOICE     Voice model (default depends on backend)
  -o, --output DIR      Output directory (default: ./output)
  -m, --models DIR      Models directory (default: ./models)
  -c, --combine         Create a combined audio file from all segments
  --combined-name       Filename for combined output (default: combined_voiceover.wav)
  --voices              Show available voice models and exit
  -h, --help            Show help message
```

### Examples

```bash
# Piper (default backend)
quickcall-voiceover config.json --combine
quickcall-voiceover -t script.txt -v en_US-ryan-high -c

# Kokoro backend
quickcall-voiceover -b kokoro -v af_heart config.json -c
quickcall-voiceover -b kokoro -v am_michael -t script.txt -c

# Use config for voice settings, text file for content
quickcall-voiceover voice_config.json -t script.txt -c

# Interactive text mode
quickcall-voiceover --text
quickcall-voiceover -b kokoro --text
```

## Voice Models

### Piper Voices

| Model ID | Name | Description |
|----------|------|-------------|
| `en_US-hfc_male-medium` | Male (US) | Clear male voice (default) |
| `en_US-hfc_female-medium` | Female (US) | Clear female voice |
| `en_US-amy-medium` | Amy (US) | Natural female voice |
| `en_US-joe-medium` | Joe (US) | Natural male voice |
| `en_US-ryan-high` | Ryan (US) | High quality male voice |
| `en_US-lessac-high` | Lessac (US) | High quality female voice |
| `en_GB-alan-medium` | Alan (UK) | British male voice |
| `en_GB-alba-medium` | Alba (UK) | British female voice |
| `en_GB-cori-high` | Cori (UK) | High quality British female |

Browse all Piper voices at [Piper samples](https://rhasspy.github.io/piper-samples/).

### Kokoro Voices

| Voice ID | Name | Description |
|----------|------|-------------|
| `af_heart` | Heart (US Female) | Warm, expressive (default) |
| `af_bella` | Bella (US Female) | Clear American female |
| `af_nicole` | Nicole (US Female) | Professional American female |
| `af_sarah` | Sarah (US Female) | Friendly American female |
| `af_sky` | Sky (US Female) | Bright American female |
| `am_adam` | Adam (US Male) | Clear American male |
| `am_michael` | Michael (US Male) | Professional American male |
| `bf_emma` | Emma (UK Female) | British female |
| `bf_isabella` | Isabella (UK Female) | Elegant British female |
| `bm_george` | George (UK Male) | British male |
| `bm_lewis` | Lewis (UK Male) | Clear British male |

More info at [Kokoro-82M on HuggingFace](https://huggingface.co/hexgrad/Kokoro-82M).

## Configuration

### Config File Format

```json
{
  "voice": {
    "backend": "piper",
    "model": "en_US-hfc_male-medium",
    "length_scale": 1.0,
    "noise_scale": 0.667,
    "noise_w": 0.8,
    "sentence_silence": 0.5
  },
  "output": {
    "format": "wav"
  },
  "segments": [
    {
      "id": "01_intro",
      "text": "Welcome to the demo."
    },
    {
      "id": "02_main",
      "text": "This is the main content."
    }
  ]
}
```

### Kokoro Config

```json
{
  "voice": {
    "backend": "kokoro",
    "model": "af_heart",
    "speed": 1.0
  },
  "output": {
    "format": "wav"
  },
  "segments": [
    {
      "id": "01_intro",
      "text": "Welcome to the demo."
    }
  ]
}
```

### Voice Settings

#### Piper Settings

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `backend` | string | `piper` | TTS backend |
| `model` | string | `en_US-hfc_male-medium` | Piper voice model |
| `length_scale` | float | `1.0` | Speech speed (lower = faster) |
| `noise_scale` | float | `0.667` | Voice variation |
| `noise_w` | float | `0.8` | Phoneme width noise |
| `sentence_silence` | float | `0.5` | Silence between sentences (seconds) |

#### Kokoro Settings

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `backend` | string | `kokoro` | TTS backend |
| `model` | string | `af_heart` | Kokoro voice ID |
| `speed` | float | `1.0` | Speech speed multiplier |

## Programmatic Usage

```python
from pathlib import Path
from quickcall_voiceover import generate_voiceover, generate_from_text

# Piper (default)
generate_voiceover(
    config_path=Path("config.json"),
    output_dir=Path("./output"),
    combine=True,
)

# Kokoro
generate_voiceover(
    config_path=Path("config.json"),
    output_dir=Path("./output"),
    combine=True,
    backend="kokoro",
    voice="af_heart",
)

# From text lines with Kokoro
lines = [
    "First line of voice over.",
    "Second line of voice over.",
]

generate_from_text(
    lines=lines,
    voice="af_heart",
    output_dir=Path("./output"),
    combine=True,
    backend="kokoro",
)
```

## Docker

Build the image:

```bash
docker build -t quickcall-voiceover .
```

Run with a config file:

```bash
docker run -v $(pwd)/config:/config -v $(pwd)/output:/app/output \
  quickcall-voiceover /config/voiceover.json --combine
```

## License

This project is licensed under Apache-2.0.

**Note:** This tool depends on:
- [Piper TTS](https://github.com/OHF-Voice/piper1-gpl) - GPL-3.0 license
- [Kokoro](https://github.com/hexgrad/kokoro) - Apache-2.0 license (trained on CC BY licensed datasets)

These are installed as separate dependencies and are not bundled with this package.

---

<p align="center">
  Built with ❤️ by <a href="https://quickcall.dev">QuickCall</a>
</p>
