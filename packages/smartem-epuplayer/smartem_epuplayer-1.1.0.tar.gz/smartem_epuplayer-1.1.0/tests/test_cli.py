import subprocess
import sys


def test_cli_help():
    result = subprocess.run(
        [sys.executable, "-m", "smartem_epuplayer", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Filesystem Recording and Replay Tool" in result.stdout


def test_cli_record_help():
    result = subprocess.run(
        [sys.executable, "-m", "smartem_epuplayer", "record", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "directory" in result.stdout.lower()
    assert "--output" in result.stdout


def test_cli_replay_help():
    result = subprocess.run(
        [sys.executable, "-m", "smartem_epuplayer", "replay", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "recording" in result.stdout.lower()
    assert "--dev-mode" in result.stdout
    assert "--fast" in result.stdout
    assert "--exact" in result.stdout


def test_cli_info_help():
    result = subprocess.run(
        [sys.executable, "-m", "smartem_epuplayer", "info", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "recording" in result.stdout.lower()


def test_module_import():
    from smartem_epuplayer import EPUEvent, EPURecorder, EPUReplayer, __version__

    assert isinstance(__version__, str) and __version__
    assert EPUEvent is not None
    assert EPURecorder is not None
    assert EPUReplayer is not None
