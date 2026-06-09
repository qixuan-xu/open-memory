import subprocess
import sys


def test_cli_lists_models():
    result = subprocess.run(
        [sys.executable, "-m", "open_memory.cli", "models", "list"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "whisper-small" in result.stdout
    assert "bge-m3" in result.stdout

