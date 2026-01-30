import time

import pytest

from smartem_epuplayer import EPURecorder, EPUReplayer
from smartem_epuplayer.models import EPUEvent


class TestEPUEvent:
    def test_create_event(self):
        event = EPUEvent(
            timestamp=time.time(),
            event_type="created",
            src_path="test/file.txt",
        )
        assert event.event_type == "created"
        assert event.src_path == "test/file.txt"
        assert event.is_directory is False

    def test_event_with_content(self):
        event = EPUEvent(
            timestamp=time.time(),
            event_type="created",
            src_path="test/file.txt",
            content="Hello, World!",
            size=13,
        )
        assert event.content == "Hello, World!"
        assert event.size == 13


class TestEPURecorder:
    def test_recorder_init(self, watch_dir, recording_file):
        recorder = EPURecorder(
            watch_dir=str(watch_dir),
            output_file=str(recording_file),
        )
        assert recorder.watch_dir == watch_dir.resolve()
        assert recorder.output_file == recording_file
        assert recorder.running is False

    def test_recorder_captures_initial_state(self, watch_dir, recording_file):
        # Create some initial files
        (watch_dir / "file1.txt").write_text("content1")
        (watch_dir / "file2.txt").write_text("content2")
        subdir = watch_dir / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").write_text("content3")

        recorder = EPURecorder(
            watch_dir=str(watch_dir),
            output_file=str(recording_file),
        )

        # Check initial events were captured
        event_paths = [e.src_path for e in recorder.events]
        assert "file1.txt" in event_paths
        assert "file2.txt" in event_paths
        assert "subdir" in event_paths
        assert "subdir/file3.txt" in event_paths


class TestEPUReplayer:
    def test_replayer_file_not_found(self, temp_dir):
        with pytest.raises(FileNotFoundError):
            EPUReplayer(
                recording_file=str(temp_dir / "nonexistent.tar.gz"),
                target_dir=str(temp_dir / "target"),
            )


class TestRoundTrip:
    def test_simple_roundtrip(self, watch_dir, target_dir, recording_file):
        # Create initial files
        (watch_dir / "hello.txt").write_text("Hello, World!")
        (watch_dir / "data.json").write_text('{"key": "value"}')
        subdir = watch_dir / "nested"
        subdir.mkdir()
        (subdir / "deep.txt").write_text("Deep content")

        # Record
        recorder = EPURecorder(
            watch_dir=str(watch_dir),
            output_file=str(recording_file),
        )
        recorder.stop_recording()

        assert recording_file.exists()

        # Replay
        replayer = EPUReplayer(
            recording_file=str(recording_file),
            target_dir=str(target_dir),
        )
        replayer.replay(burst_mode=True, verify_integrity=True)

        # Verify
        assert (target_dir / "hello.txt").exists()
        assert (target_dir / "hello.txt").read_text() == "Hello, World!"
        assert (target_dir / "data.json").exists()
        assert (target_dir / "data.json").read_text() == '{"key": "value"}'
        assert (target_dir / "nested" / "deep.txt").exists()
        assert (target_dir / "nested" / "deep.txt").read_text() == "Deep content"

    def test_binary_placeholder_mode(self, watch_dir, target_dir, recording_file):
        # Create a file that will be treated as binary (based on content detection)
        binary_content = b"\x00\x01\x02\x03\x04\x05"
        (watch_dir / "binary.bin").write_bytes(binary_content)
        (watch_dir / "text.txt").write_text("Plain text")

        # Record with binary placeholder mode (default)
        recorder = EPURecorder(
            watch_dir=str(watch_dir),
            output_file=str(recording_file),
            skip_binary_content=True,
        )
        recorder.stop_recording()

        # Check that binary file was marked as placeholder
        binary_events = [e for e in recorder.events if e.src_path == "binary.bin"]
        assert len(binary_events) == 1
        assert binary_events[0].is_placeholder is True

        # Replay
        replayer = EPUReplayer(
            recording_file=str(recording_file),
            target_dir=str(target_dir),
        )
        replayer.replay(burst_mode=True, verify_integrity=False)

        # Text file should be intact
        assert (target_dir / "text.txt").read_text() == "Plain text"

        # Binary file should exist as placeholder (null bytes)
        assert (target_dir / "binary.bin").exists()
