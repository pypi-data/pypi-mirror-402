import hashlib
import json
import os
import shutil
import sys
import tarfile
import tempfile
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from .models import EPUEvent


class EPURecorder(FileSystemEventHandler):
    def __init__(
        self,
        watch_dir: str,
        output_file: str,
        skip_binary_content: bool = True,
        force_text_extensions: list[str] | None = None,
        force_binary_extensions: list[str] | None = None,
    ):
        self.watch_dir = Path(watch_dir).resolve()
        self.output_file = Path(output_file)
        self.events: list[EPUEvent] = []
        self.observer = Observer()
        self.running = False

        # Binary content handling settings
        self.skip_binary_content = skip_binary_content
        self.force_text_extensions = {ext.lower().lstrip(".") for ext in (force_text_extensions or [])}
        self.force_binary_extensions = {ext.lower().lstrip(".") for ext in (force_binary_extensions or [])}

        # Track file states for diff calculation
        self.file_states: dict[str, dict[str, Any]] = {}
        self.binary_chunks: dict[str, bytes] = {}
        self.chunk_counter = 0

        # Track unreadable files for reporting
        self.unreadable_files: list[str] = []

        # Track placeholder files for reporting
        self.placeholder_files: list[str] = []

        # Create temp directory for binary chunks
        self.temp_dir = Path(tempfile.mkdtemp(prefix="epurecorder_"))

        # Capture initial state
        self._capture_initial_state()

    def _normalize_path(self, path: Path) -> str:
        return str(PurePosixPath(path))

    def _is_binary_file(self, file_path: Path) -> bool:
        file_extension = file_path.suffix.lower().lstrip(".")

        # Check extension overrides first
        if file_extension in self.force_text_extensions:
            return False
        if file_extension in self.force_binary_extensions:
            return True

        # Common text file extensions
        text_extensions = {
            "txt",
            "md",
            "json",
            "xml",
            "html",
            "htm",
            "css",
            "js",
            "py",
            "java",
            "cpp",
            "c",
            "h",
            "hpp",
            "cs",
            "php",
            "rb",
            "go",
            "rs",
            "sh",
            "bat",
            "ps1",
            "yml",
            "yaml",
            "toml",
            "ini",
            "cfg",
            "conf",
            "log",
            "csv",
            "tsv",
            "sql",
            "r",
            "tex",
            "latex",
            "rtf",
            "dockerfile",
            "makefile",
            "gitignore",
            "gitattributes",
            "license",
            "readme",
            "dm",  # Add dm as text based on your use case
        }

        # Common binary file extensions
        binary_extensions = {
            "jpg",
            "jpeg",
            "png",
            "gif",
            "bmp",
            "tiff",
            "tif",
            "webp",
            "ico",
            "svg",
            "mp4",
            "avi",
            "mov",
            "wmv",
            "flv",
            "mkv",
            "webm",
            "mp3",
            "wav",
            "flac",
            "ogg",
            "pdf",
            "doc",
            "docx",
            "ppt",
            "pptx",
            "xls",
            "xlsx",
            "zip",
            "rar",
            "7z",
            "tar",
            "gz",
            "bz2",
            "xz",
            "exe",
            "dll",
            "so",
            "dylib",
            "bin",
            "dat",
            "db",
            "sqlite",
            "mrc",  # Add mrc as binary based on your use case
        }

        if file_extension in text_extensions:
            return False
        if file_extension in binary_extensions:
            return True

        # For unknown extensions, try to detect by content
        try:
            with open(file_path, "rb") as f:
                chunk = f.read(1024)  # Read first 1KB
                if not chunk:
                    return False  # Empty file, treat as text

                # Check for null bytes (common in binary files)
                if b"\x00" in chunk:
                    return True

                # Check if content is mostly printable ASCII
                try:
                    chunk.decode("utf-8")
                    return False  # Successfully decoded as UTF-8, likely text
                except UnicodeDecodeError:
                    return True  # Cannot decode as UTF-8, likely binary
        except (PermissionError, OSError):
            # If we can't read the file, default to text
            return False

    def _should_use_placeholder(self, file_path: Path) -> bool:
        if not self.skip_binary_content:
            return False
        return self._is_binary_file(file_path)

    def _calculate_file_hash(self, file_path: Path) -> str:
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except (PermissionError, OSError) as e:
            print(f"Warning: Cannot read file {file_path}: {e}")
            # Track unreadable file for reporting
            self.unreadable_files.append(str(file_path))
            # Return a special hash to indicate the file couldn't be read
            return f"unreadable_{file_path.stat().st_size}_{file_path.stat().st_mtime}"

    def _store_binary_chunk(self, content: bytes) -> str:
        chunk_id = f"chunk_{self.chunk_counter}"
        self.chunk_counter += 1

        chunk_file = self.temp_dir / f"{chunk_id}.bin"
        chunk_file.write_bytes(content)

        return chunk_id

    def _capture_initial_state(self):
        print(f"Capturing initial state of {self.watch_dir}")
        for root, _dirs, files in os.walk(self.watch_dir):
            root_path = Path(root)

            # Record directory creation
            if root_path != self.watch_dir:
                rel_path = root_path.relative_to(self.watch_dir)
                norm_path = self._normalize_path(rel_path)
                event = EPUEvent(timestamp=time.time(), event_type="initial_dir", src_path=norm_path, is_directory=True)
                self.events.append(event)

            # Record file creation
            for file in files:
                file_path = root_path / file
                rel_path = file_path.relative_to(self.watch_dir)
                norm_path = self._normalize_path(rel_path)

                size = file_path.stat().st_size
                content_hash = self._calculate_file_hash(file_path)

                # Store initial file state
                self.file_states[norm_path] = {"size": size, "hash": content_hash, "content": None}

                content = None
                binary_chunk_id = None
                is_placeholder = self._should_use_placeholder(file_path)

                if is_placeholder:
                    # Create placeholder - store only size information
                    self.placeholder_files.append(str(file_path))
                    # Don't store any content for placeholders
                elif size < 1024 * 1024:  # 1MB limit for inline content
                    try:
                        content = file_path.read_text(encoding="utf-8", errors="ignore")
                        self.file_states[norm_path]["content"] = content
                    except Exception:
                        # Binary file or permission error - try to store as chunk
                        try:
                            binary_content = file_path.read_bytes()
                            binary_chunk_id = self._store_binary_chunk(binary_content)
                        except (PermissionError, OSError) as e:
                            print(f"Warning: Cannot read file content for {file_path}: {e}")
                            # Track unreadable file for reporting
                            self.unreadable_files.append(str(file_path))
                            # Skip storing content for unreadable files
                            pass
                else:
                    # Large file - store as chunk
                    try:
                        binary_content = file_path.read_bytes()
                        binary_chunk_id = self._store_binary_chunk(binary_content)
                    except (PermissionError, OSError) as e:
                        print(f"Warning: Cannot read large file content for {file_path}: {e}")
                        # Track unreadable file for reporting
                        self.unreadable_files.append(str(file_path))
                        # Skip storing content for unreadable files
                        pass

                # Get file timestamps
                stat = file_path.stat()

                event = EPUEvent(
                    timestamp=time.time(),
                    event_type="initial_file",
                    src_path=norm_path,
                    is_directory=False,
                    content=content,
                    size=size,
                    content_hash=content_hash,
                    binary_chunk_id=binary_chunk_id,
                    operation_data={"mtime": stat.st_mtime, "atime": stat.st_atime},
                    is_placeholder=is_placeholder,
                )
                self.events.append(event)

    def on_created(self, event: FileSystemEvent):
        self._record_event(event, "created")

    def on_modified(self, event: FileSystemEvent):
        self._record_event(event, "modified")

    def on_deleted(self, event: FileSystemEvent):
        self._record_event(event, "deleted")

    def on_moved(self, event: FileSystemEvent):
        src_rel = Path(event.src_path).relative_to(self.watch_dir)
        dest_rel = Path(event.dest_path).relative_to(self.watch_dir)

        src_norm = self._normalize_path(src_rel)
        dest_norm = self._normalize_path(dest_rel)

        # Update file state tracking
        if src_norm in self.file_states:
            self.file_states[dest_norm] = self.file_states.pop(src_norm)

        fs_event = EPUEvent(
            timestamp=time.time(),
            event_type="moved",
            src_path=src_norm,
            dest_path=dest_norm,
            is_directory=event.is_directory,
        )
        self.events.append(fs_event)
        print(f"MOVED: {src_norm} -> {dest_norm}")

    def _record_event(self, event: FileSystemEvent, event_type: str):
        event_path = Path(event.src_path)
        rel_path = event_path.relative_to(self.watch_dir)
        norm_path = self._normalize_path(rel_path)

        if event.is_directory:
            # Handle directory events
            fs_event = EPUEvent(
                timestamp=time.time(),
                event_type=event_type,
                src_path=norm_path,
                is_directory=True,
            )
            self.events.append(fs_event)
            print(f"{event_type.upper()}: {norm_path}")
            return

        # Handle file events with diff-based recording
        if event_type == "deleted":
            # Remove from state tracking
            self.file_states.pop(norm_path, None)
            fs_event = EPUEvent(
                timestamp=time.time(),
                event_type=event_type,
                src_path=norm_path,
                is_directory=False,
            )
            self.events.append(fs_event)
            print(f"DELETED: {norm_path}")
            return

        if not event_path.exists():
            return

        # Get current file state
        current_size = event_path.stat().st_size
        current_hash = self._calculate_file_hash(event_path)

        # Check if this is a new file or modification
        if event_type == "created" or norm_path not in self.file_states:
            self._record_file_creation(event_path, norm_path, current_size, current_hash)
        else:
            self._record_file_modification(event_path, norm_path, current_size, current_hash)

    def _record_file_creation(self, file_path: Path, norm_path: str, size: int, content_hash: str):
        content = None
        binary_chunk_id = None
        is_placeholder = self._should_use_placeholder(file_path)

        if is_placeholder:
            # Create placeholder - store only size information
            self.placeholder_files.append(str(file_path))
            # Don't store any content for placeholders
        elif size < 1024 * 1024:  # 1MB limit
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                try:
                    binary_content = file_path.read_bytes()
                    binary_chunk_id = self._store_binary_chunk(binary_content)
                except (PermissionError, OSError) as e:
                    print(f"Warning: Cannot read file content for {file_path}: {e}")
                    # Track unreadable file for reporting
                    self.unreadable_files.append(str(file_path))
                    # Skip storing content for unreadable files
                    pass
        else:
            try:
                binary_content = file_path.read_bytes()
                binary_chunk_id = self._store_binary_chunk(binary_content)
            except (PermissionError, OSError) as e:
                print(f"Warning: Cannot read large file content for {file_path}: {e}")
                # Track unreadable file for reporting
                self.unreadable_files.append(str(file_path))
                # Skip storing content for unreadable files
                pass

        # Update state tracking
        self.file_states[norm_path] = {"size": size, "hash": content_hash, "content": content}

        fs_event = EPUEvent(
            timestamp=time.time(),
            event_type="created",
            src_path=norm_path,
            is_directory=False,
            content=content,
            size=size,
            content_hash=content_hash,
            binary_chunk_id=binary_chunk_id,
            is_placeholder=is_placeholder,
        )
        self.events.append(fs_event)
        print(f"CREATED: {norm_path}" + (" (binary placeholder)" if is_placeholder else ""))

    def _record_file_modification(self, file_path: Path, norm_path: str, current_size: int, current_hash: str):
        old_state = self.file_states.get(norm_path, {})
        old_size = old_state.get("size", 0)
        old_hash = old_state.get("hash", "")

        # Skip if file hasn't actually changed
        if current_hash == old_hash:
            return

        # Determine modification type
        if current_size > old_size:
            # Likely an append operation
            self._record_append_operation(file_path, norm_path, old_size, current_size, current_hash)
        elif current_size < old_size:
            # File was truncated
            self._record_truncate_operation(file_path, norm_path, current_size, current_hash)
        else:
            # Same size but different content - full modification
            self._record_full_modification(file_path, norm_path, current_size, current_hash)

    def _record_append_operation(self, file_path: Path, norm_path: str, old_size: int, new_size: int, new_hash: str):
        try:
            # Read only the appended content
            try:
                with open(file_path, "rb") as f:
                    f.seek(old_size)
                    appended_content = f.read(new_size - old_size)

                # Try to decode as text, otherwise store as binary
                append_data = None
                binary_chunk_id = None

                try:
                    append_data = appended_content.decode("utf-8")
                except Exception:
                    binary_chunk_id = self._store_binary_chunk(appended_content)
            except (PermissionError, OSError) as e:
                print(f"Warning: Cannot read appended content for {file_path}: {e}")
                # Track unreadable file for reporting
                self.unreadable_files.append(str(file_path))
                # Skip storing content for unreadable files
                append_data = None
                binary_chunk_id = None

            # Update state
            self.file_states[norm_path].update({"size": new_size, "hash": new_hash})

            fs_event = EPUEvent(
                timestamp=time.time(),
                event_type="appended",
                src_path=norm_path,
                is_directory=False,
                content=append_data,
                size=new_size,
                content_hash=new_hash,
                binary_chunk_id=binary_chunk_id,
                file_position=old_size,
                operation_data={"append_size": new_size - old_size},
            )
            self.events.append(fs_event)
            print(f"APPENDED: {norm_path} (+{new_size - old_size} bytes)")

        except Exception as e:
            print(f"Error recording append for {norm_path}: {e}")
            self._record_full_modification(file_path, norm_path, new_size, new_hash)

    def _record_truncate_operation(self, file_path: Path, norm_path: str, new_size: int, new_hash: str):
        # Update state
        self.file_states[norm_path].update({"size": new_size, "hash": new_hash})

        fs_event = EPUEvent(
            timestamp=time.time(),
            event_type="truncated",
            src_path=norm_path,
            is_directory=False,
            size=new_size,
            content_hash=new_hash,
            operation_data={"new_size": new_size},
        )
        self.events.append(fs_event)
        print(f"TRUNCATED: {norm_path} to {new_size} bytes")

    def _record_full_modification(self, file_path: Path, norm_path: str, size: int, content_hash: str):
        content = None
        binary_chunk_id = None
        is_placeholder = self._should_use_placeholder(file_path)

        if is_placeholder:
            # For placeholder files, just track the size change
            if str(file_path) not in self.placeholder_files:
                self.placeholder_files.append(str(file_path))
        elif size < 1024 * 1024:  # 1MB limit
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                self.file_states[norm_path]["content"] = content
            except Exception:
                try:
                    binary_content = file_path.read_bytes()
                    binary_chunk_id = self._store_binary_chunk(binary_content)
                except (PermissionError, OSError) as e:
                    print(f"Warning: Cannot read file content for {file_path}: {e}")
                    # Track unreadable file for reporting
                    self.unreadable_files.append(str(file_path))
                    # Skip storing content for unreadable files
                    pass
        else:
            try:
                binary_content = file_path.read_bytes()
                binary_chunk_id = self._store_binary_chunk(binary_content)
            except (PermissionError, OSError) as e:
                print(f"Warning: Cannot read large file content for {file_path}: {e}")
                # Track unreadable file for reporting
                self.unreadable_files.append(str(file_path))
                # Skip storing content for unreadable files
                pass

        # Update state
        self.file_states[norm_path].update({"size": size, "hash": content_hash})

        fs_event = EPUEvent(
            timestamp=time.time(),
            event_type="modified",
            src_path=norm_path,
            is_directory=False,
            content=content,
            size=size,
            content_hash=content_hash,
            binary_chunk_id=binary_chunk_id,
            is_placeholder=is_placeholder,
        )
        self.events.append(fs_event)
        print(f"MODIFIED: {norm_path}" + (" (binary placeholder)" if is_placeholder else ""))

    def start_recording(self):
        print(f"Starting recording of {self.watch_dir}")
        print(f"Recording will be saved to {self.output_file}")
        print("Press Ctrl+C to stop recording")

        self.observer.schedule(self, str(self.watch_dir), recursive=True)
        self.observer.start()
        self.running = True

        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop_recording()

    def stop_recording(self):
        print("\nStopping recording...")
        self.running = False
        if self.observer.is_alive():
            self.observer.stop()
            self.observer.join()

        # Create tar.gz archive
        self._create_archive()

        # Cleanup temp directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)

        print(f"Recording saved to {self.output_file}")
        print(f"Captured {len(self.events)} events")

        # Report unreadable files
        unique_unreadable = list(set(self.unreadable_files))
        if unique_unreadable:
            print(f"\nUnreadable files report ({len(unique_unreadable)} files):")
            for file_path in sorted(unique_unreadable):
                print(f"  - {file_path}")
            print(
                "\nNote: These files were tracked but their content could not be read due to permission restrictions."
            )
        else:
            print("\nAll files were readable during recording.")

        # Report placeholder files
        unique_placeholders = list(set(self.placeholder_files))
        if unique_placeholders:
            print(f"\nBinary placeholder files report ({len(unique_placeholders)} files):")
            for file_path in sorted(unique_placeholders):
                print(f"  - {file_path}")
            print("\nNote: These binary files were replaced with empty placeholders to reduce archive size.")

    def _create_archive(self):
        print("\nPacking recording data...")

        # Prepare recording data
        events_data = [asdict(event) for event in self.events]
        recording = {
            "metadata": {
                "recorded_at": datetime.now().isoformat(),
                "watch_dir": str(self.watch_dir),
                "total_events": len(self.events),
                "version": "2.0",
                "platform": sys.platform,
            },
            "events": events_data,
        }

        # Create recording.json in temp directory
        print("Creating recording metadata...")
        recording_file = self.temp_dir / "recording.json"
        recording_file.write_text(json.dumps(recording, indent=2))

        # Create tar.gz archive
        print("Creating compressed archive...")
        chunk_count = len(list(self.temp_dir.glob("*.bin")))
        with tarfile.open(self.output_file, "w:gz") as tar:
            # Add recording.json
            tar.add(recording_file, arcname="recording.json")

            # Add all binary chunks
            if chunk_count > 0:
                print(f"Packing {chunk_count} binary chunks...")
            for chunk_file in self.temp_dir.glob("*.bin"):
                tar.add(chunk_file, arcname=f"chunks/{chunk_file.name}")

        print(f"Archive created with {chunk_count} binary chunks")
        print(f"Packing complete: {self.output_file}")
