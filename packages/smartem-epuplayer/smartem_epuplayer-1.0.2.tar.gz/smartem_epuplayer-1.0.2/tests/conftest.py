import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory(prefix="epuplayer_test_") as d:
        yield Path(d)


@pytest.fixture
def watch_dir(temp_dir):
    watch = temp_dir / "watch"
    watch.mkdir()
    return watch


@pytest.fixture
def target_dir(temp_dir):
    target = temp_dir / "target"
    target.mkdir()
    return target


@pytest.fixture
def recording_file(temp_dir):
    return temp_dir / "recording.tar.gz"
