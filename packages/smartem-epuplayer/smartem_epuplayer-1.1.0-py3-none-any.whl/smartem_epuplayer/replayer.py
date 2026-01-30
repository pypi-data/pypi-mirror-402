import hashlib
import json
import os
import shutil
import tarfile
import tempfile
import time
from pathlib import Path, PurePosixPath

from .models import EPUEvent


class EPUReplayer:
    def __init__(self, recording_file: str, target_dir: str):
        self.recording_file = Path(recording_file)
        self.target_dir = Path(target_dir)
        self.events: list[EPUEvent] = []
        self.chunks_dir: Path | None = None
        self.temp_dir: Path | None = None
        self.metadata: dict = {}

        self._load_recording()

    def _load_recording(self):
        if not self.recording_file.exists():
            raise FileNotFoundError(f"Recording file not found: {self.recording_file}")

        # Check if it's a tar.gz archive or legacy JSON
        if self.recording_file.suffix.lower() == ".gz" or tarfile.is_tarfile(self.recording_file):
            self._load_from_archive()
        else:
            self._load_from_json()

        print(f"Loaded recording with {len(self.events)} events")
        print(f"Recorded from: {self.metadata['watch_dir']}")
        print(f"Recorded at: {self.metadata['recorded_at']}")

    def _load_from_archive(self):
        print("\nUnpacking recording archive...")
        self.temp_dir = Path(tempfile.mkdtemp(prefix="epureplayer_"))

        print("Extracting archive contents...")
        with tarfile.open(self.recording_file, "r:gz") as tar:
            tar.extractall(self.temp_dir)

        # Load recording.json
        print("Loading recording metadata...")
        recording_file = self.temp_dir / "recording.json"
        if not recording_file.exists():
            raise ValueError("Invalid archive: missing recording.json")

        data = json.loads(recording_file.read_text())
        self.metadata = data["metadata"]

        # Set chunks directory
        self.chunks_dir = self.temp_dir / "chunks"

        # Count binary chunks
        chunk_count = len(list(self.chunks_dir.glob("*.bin"))) if self.chunks_dir.exists() else 0
        if chunk_count > 0:
            print(f"Found {chunk_count} binary chunks")

        print("Processing events...")
        for event_data in data["events"]:
            event = EPUEvent(**event_data)
            self.events.append(event)

        print(f"Unpacking complete: {len(self.events)} events loaded")

    def _load_from_json(self):
        data = json.loads(self.recording_file.read_text())
        self.metadata = data["metadata"]

        for event_data in data["events"]:
            event = EPUEvent(**event_data)
            self.events.append(event)

    def _normalize_target_path(self, src_path: str) -> Path:
        # Convert POSIX path to target platform
        posix_path = PurePosixPath(src_path)
        return self.target_dir / Path(*posix_path.parts)

    def _load_binary_chunk(self, chunk_id: str) -> bytes:
        if not self.chunks_dir:
            raise ValueError("No chunks directory available")

        chunk_file = self.chunks_dir / f"{chunk_id}.bin"
        if not chunk_file.exists():
            raise FileNotFoundError(f"Binary chunk not found: {chunk_id}")

        return chunk_file.read_bytes()

    def _is_unreadable_file(self, event: EPUEvent) -> bool:
        return event.content_hash is not None and event.content_hash.startswith("unreadable_")

    def replay(
        self,
        speed_multiplier: float = 1.0,
        verify_integrity: bool = True,
        max_delay: float | None = None,
        burst_mode: bool = False,
        skip_unreadable: bool = False,
    ):
        print(f"Replaying to {self.target_dir}")

        if burst_mode:
            print("Burst mode: Processing events as fast as possible")
        else:
            print(f"Speed multiplier: {speed_multiplier}x")
            if max_delay:
                print(f"Maximum delay capped at: {max_delay}s")

        # Create target directory
        self.target_dir.mkdir(parents=True, exist_ok=True)

        verification_errors = []
        skipped_unreadable_count = 0
        start_time = time.time()
        total_original_duration = 0

        if len(self.events) > 1:
            total_original_duration = self.events[-1].timestamp - self.events[0].timestamp

        try:
            for i, event in enumerate(self.events):
                # Calculate and apply delay
                if i > 0 and not burst_mode:
                    time_diff = event.timestamp - self.events[i - 1].timestamp
                    delay = time_diff / speed_multiplier

                    # Apply maximum delay cap if specified
                    if max_delay and delay > max_delay:
                        delay = max_delay

                    # Minimum delay to prevent overwhelming the system
                    if delay > 0.001:  # 1ms minimum
                        time.sleep(delay)
                elif burst_mode and i > 0:
                    # Minimal delay in burst mode to prevent system overload
                    time.sleep(0.001)

                was_skipped = self._replay_event(event, skip_unreadable=skip_unreadable)
                if was_skipped:
                    skipped_unreadable_count += 1

                # Verify integrity after certain operations
                if (
                    verify_integrity
                    and event.content_hash
                    and not event.is_directory
                    and not self._is_unreadable_file(event)
                ):
                    error = self._verify_file_integrity(event)
                    if error:
                        verification_errors.append(error)

                # Progress indicator with timing info
                if i % 50 == 0:  # Every 50 events for better performance
                    elapsed = time.time() - start_time
                    progress_pct = ((i + 1) / len(self.events)) * 100
                    print(f"Progress: {i + 1}/{len(self.events)} events ({progress_pct:.1f}%) - {elapsed:.1f}s elapsed")

            elapsed_total = time.time() - start_time
            print(f"\nReplay completed in {elapsed_total:.1f}s!")

            if total_original_duration > 0:
                compression_ratio = total_original_duration / elapsed_total
                print(f"Time compression: {compression_ratio:.1f}x (original: {total_original_duration:.1f}s)")

            if skip_unreadable and skipped_unreadable_count > 0:
                print(f"\nSkipped {skipped_unreadable_count} unreadable files during replay.")

            if verification_errors:
                print(f"\nIntegrity verification found {len(verification_errors)} issues:")
                for error in verification_errors[:5]:  # Show first 5 errors
                    print(f"  - {error}")
                if len(verification_errors) > 5:
                    print(f"  ... and {len(verification_errors) - 5} more")
            else:
                print("\nIntegrity verification passed!")

        finally:
            # Cleanup temp directory if created
            if self.temp_dir and self.temp_dir.exists():
                shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _verify_file_integrity(self, event: EPUEvent) -> str | None:
        if not event.content_hash:
            return None

        target_path = self._normalize_target_path(event.src_path)

        if not target_path.exists():
            return f"File missing after replay: {event.src_path}"

        try:
            actual_hash = self._calculate_file_hash(target_path)
            if actual_hash != event.content_hash:
                return (
                    f"Hash mismatch for {event.src_path}: "
                    f"expected {event.content_hash[:8]}..., got {actual_hash[:8]}..."
                )
        except Exception as e:
            return f"Error verifying {event.src_path}: {e}"

        return None

    def _calculate_file_hash(self, file_path: Path) -> str:
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def _replay_event(self, event: EPUEvent, skip_unreadable: bool = False) -> bool:
        target_path = self._normalize_target_path(event.src_path)

        # Skip unreadable files if requested
        if skip_unreadable and self._is_unreadable_file(event):
            print(f"Skipped unreadable file: {event.src_path}")
            return True

        try:
            if event.event_type in ["initial_dir", "created"] and event.is_directory:
                target_path.mkdir(parents=True, exist_ok=True)
                print(f"Created directory: {event.src_path}")

            elif event.event_type in ["initial_file", "created"] and not event.is_directory:
                self._replay_file_creation(event, target_path)

            elif event.event_type == "modified" and not event.is_directory:
                self._replay_file_modification(event, target_path)

            elif event.event_type == "appended" and not event.is_directory:
                self._replay_file_append(event, target_path)

            elif event.event_type == "truncated" and not event.is_directory:
                self._replay_file_truncate(event, target_path)

            elif event.event_type == "deleted":
                if target_path.exists():
                    if event.is_directory:
                        shutil.rmtree(target_path)
                    else:
                        target_path.unlink()
                    print(f"Deleted: {event.src_path}")

            elif event.event_type == "moved":
                dest_path = self._normalize_target_path(event.dest_path)
                if target_path.exists():
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(target_path), str(dest_path))
                    print(f"Moved: {event.src_path} -> {event.dest_path}")

        except Exception as e:
            print(f"Error replaying event {event.event_type} for {event.src_path}: {e}")

        return False

    def _replay_file_creation(self, event: EPUEvent, target_path: Path):
        target_path.parent.mkdir(parents=True, exist_ok=True)

        if getattr(event, "is_placeholder", False):
            # Create empty placeholder file with correct size
            with open(target_path, "wb") as f:
                if event.size:
                    f.write(b"\0" * event.size)
            print(f"Created binary placeholder file: {event.src_path} ({event.size} bytes)")
        elif event.content is not None:
            # Text content
            target_path.write_text(event.content)
            print(f"Created file: {event.src_path}")
        elif event.binary_chunk_id:
            # Binary content from chunk
            binary_content = self._load_binary_chunk(event.binary_chunk_id)
            target_path.write_bytes(binary_content)
            print(f"Created file: {event.src_path}")
        else:
            # Create empty file with correct size
            with open(target_path, "wb") as f:
                if event.size:
                    f.write(b"\0" * event.size)
            print(f"Created file: {event.src_path}")

        # Set timestamps if available
        if event.operation_data and "mtime" in event.operation_data:
            try:
                mtime = event.operation_data["mtime"]
                atime = event.operation_data.get("atime", mtime)
                os.utime(target_path, (atime, mtime))
            except Exception as e:
                print(f"Warning: Could not set timestamps for {event.src_path}: {e}")

    def _replay_file_modification(self, event: EPUEvent, target_path: Path):
        if not target_path.exists():
            print(f"Warning: Cannot modify non-existent file {event.src_path}")
            return

        if getattr(event, "is_placeholder", False):
            # For placeholder files, just update the size
            with open(target_path, "r+b") as f:
                f.truncate(event.size or 0)
                if event.size:
                    f.seek(0)
                    f.write(b"\0" * event.size)
            print(f"Modified binary placeholder file: {event.src_path} ({event.size} bytes)")
        elif event.content is not None:
            # Text content - full replacement
            target_path.write_text(event.content)
            print(f"Modified file: {event.src_path}")
        elif event.binary_chunk_id:
            # Binary content - full replacement
            binary_content = self._load_binary_chunk(event.binary_chunk_id)
            target_path.write_bytes(binary_content)
            print(f"Modified file: {event.src_path}")
        else:
            print(f"Modified file: {event.src_path}")

    def _replay_file_append(self, event: EPUEvent, target_path: Path):
        if not target_path.exists():
            print(f"Warning: Cannot append to non-existent file {event.src_path}")
            return

        # Position to append location
        if event.file_position is not None:
            # Ensure file is the correct size before append
            current_size = target_path.stat().st_size
            if current_size != event.file_position:
                print(
                    f"Warning: File size mismatch for {event.src_path}. "
                    f"Expected {event.file_position}, got {current_size}"
                )

        if event.content is not None:
            # Text append
            with open(target_path, "a", encoding="utf-8") as f:
                f.write(event.content)
        elif event.binary_chunk_id:
            # Binary append
            binary_content = self._load_binary_chunk(event.binary_chunk_id)
            with open(target_path, "ab") as f:
                f.write(binary_content)

        append_size = event.operation_data.get("append_size", 0) if event.operation_data else 0
        print(f"Appended to file: {event.src_path} (+{append_size} bytes)")

    def _replay_file_truncate(self, event: EPUEvent, target_path: Path):
        if not target_path.exists():
            print(f"Warning: Cannot truncate non-existent file {event.src_path}")
            return

        new_size = event.operation_data.get("new_size", 0) if event.operation_data else 0

        with open(target_path, "r+b") as f:
            f.truncate(new_size)

        print(f"Truncated file: {event.src_path} to {new_size} bytes")
