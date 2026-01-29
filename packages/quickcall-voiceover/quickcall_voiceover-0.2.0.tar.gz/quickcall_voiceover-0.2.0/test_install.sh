#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
DIM='\033[2m'
NC='\033[0m' # No Color

# Helper to print command before running
run_cmd() {
    echo -e "${DIM}\$ $@${NC}"
    "$@"
}

echo -e "${CYAN}"
echo "╭──────────────────────────────────────────────────────────╮"
echo "│  QuickCall VoiceOver - Installation Test                 │"
echo "╰──────────────────────────────────────────────────────────╯"
echo -e "${NC}"

# Test directory
TEST_DIR="/tmp/quickcall-voiceover-test"

# Cleanup previous test
if [ -d "$TEST_DIR" ]; then
    echo -e "${YELLOW}Cleaning up previous test directory...${NC}"
    run_cmd rm -rf "$TEST_DIR"
fi

# Create test directory
echo -e "${CYAN}Creating test directory${NC}"
run_cmd mkdir -p "$TEST_DIR"
cd "$TEST_DIR"
echo ""

# Initialize uv project
echo -e "${CYAN}Initializing uv project${NC}"
run_cmd uv init --name voiceover-test
echo ""

# Install from local path
PACKAGE_PATH="/Users/sagar/work/all-things-quickcall/voice-over"
echo -e "${CYAN}Installing quickcall-voiceover${NC}"
run_cmd uv add "$PACKAGE_PATH"
echo ""

# Verify installation
echo -e "${GREEN}✓ Package installed${NC}"
echo ""

# Test 1: Show help
echo -e "${YELLOW}━━━ Test 1: CLI Help ━━━${NC}"
run_cmd uv run quickcall-voiceover --help
echo ""

# Test 2: Show voices
echo -e "${YELLOW}━━━ Test 2: Show Voices ━━━${NC}"
run_cmd uv run quickcall-voiceover --voices
echo ""

# Test 3: Config-based generation
echo -e "${YELLOW}━━━ Test 3: Config-based Generation ━━━${NC}"

# Create test config
cat > test_config.json << 'CONFIGEOF'
{
  "voice": {
    "model": "en_US-hfc_male-medium",
    "length_scale": 1.0,
    "noise_scale": 0.667,
    "noise_w": 0.8,
    "sentence_silence": 0.3
  },
  "output": {
    "format": "wav"
  },
  "segments": [
    {
      "id": "01_hello",
      "text": "Hello! This is a test of QuickCall VoiceOver."
    },
    {
      "id": "02_features",
      "text": "This tool generates high quality voice overs from text."
    },
    {
      "id": "03_goodbye",
      "text": "Thanks for testing. Goodbye!"
    }
  ]
}
CONFIGEOF

echo -e "${CYAN}Created test_config.json${NC}"
run_cmd cat test_config.json
echo ""

run_cmd uv run quickcall-voiceover test_config.json --combine
echo ""

echo -e "${GREEN}Generated files:${NC}"
run_cmd ls -lah output/
echo ""

# Test 4: Programmatic API test
echo -e "${YELLOW}━━━ Test 4: Programmatic API ━━━${NC}"

# Create a simple Python script to test programmatic usage
cat > test_programmatic.py << 'PYEOF'
from pathlib import Path
from quickcall_voiceover import generate_from_text

lines = [
    "This is a programmatic test.",
    "Generated using the Python API.",
    "QuickCall VoiceOver works great!"
]

success = generate_from_text(
    lines=lines,
    voice="en_US-hfc_male-medium",
    output_dir=Path("./output_programmatic"),
    combine=True,
    combined_filename="programmatic_combined.wav",
)

print(f"\nProgrammatic test: {'SUCCESS' if success else 'FAILED'}")
PYEOF

echo -e "${CYAN}Created test_programmatic.py${NC}"
run_cmd cat test_programmatic.py
echo ""

run_cmd uv run python test_programmatic.py
echo ""

echo -e "${GREEN}Programmatic output:${NC}"
run_cmd ls -lah output_programmatic/
echo ""

# Summary
echo -e "${CYAN}"
echo "╭──────────────────────────────────────────────────────────╮"
echo "│  Test Summary                                            │"
echo "╰──────────────────────────────────────────────────────────╯"
echo -e "${NC}"

echo -e "${GREEN}✓ CLI help works${NC}"
echo -e "${GREEN}✓ Voice listing works${NC}"
echo -e "${GREEN}✓ Config-based generation works${NC}"
echo -e "${GREEN}✓ Programmatic API works${NC}"
echo ""

echo -e "${CYAN}Test directory: $TEST_DIR${NC}"
echo -e "${CYAN}To clean up: rm -rf $TEST_DIR${NC}"
echo ""

echo -e "${GREEN}All tests completed successfully!${NC}"
