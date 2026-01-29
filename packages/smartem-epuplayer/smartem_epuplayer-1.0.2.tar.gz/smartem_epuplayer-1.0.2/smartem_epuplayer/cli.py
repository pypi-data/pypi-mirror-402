import argparse
import json
import signal
import sys
import tarfile
import tempfile
from pathlib import Path

from smartem_epuplayer.recorder import EPURecorder
from smartem_epuplayer.replayer import EPUReplayer


def main():
    parser = argparse.ArgumentParser(description="Filesystem Recording and Replay Tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Record command
    record_parser = subparsers.add_parser("record", help="Record filesystem changes")
    record_parser.add_argument("directory", help="Directory to monitor")
    record_parser.add_argument("-o", "--output", required=True, help="Output recording file (.tar.gz)")
    record_parser.add_argument(
        "--skip-binary-content",
        action="store_true",
        default=True,
        help="Replace binary files with empty placeholders (default: True)",
    )
    record_parser.add_argument(
        "--no-skip-binary-content",
        action="store_false",
        dest="skip_binary_content",
        help="Store full content of binary files (overrides --skip-binary-content)",
    )
    record_parser.add_argument(
        "--force-text-extensions",
        nargs="*",
        default=[],
        help="File extensions to always treat as text (e.g., --force-text-extensions dm dat)",
    )
    record_parser.add_argument(
        "--force-binary-extensions",
        nargs="*",
        default=[],
        help="File extensions to always treat as binary (e.g., --force-binary-extensions log txt)",
    )

    # Replay command
    replay_parser = subparsers.add_parser("replay", help="Replay filesystem changes")
    replay_parser.add_argument("recording", help="Recording file to replay (.tar.gz or legacy .json)")
    replay_parser.add_argument("target", help="Target directory for replay")
    replay_parser.add_argument(
        "-s",
        "--speed",
        type=float,
        default=1.0,
        help="Speed multiplier for custom mode (default behavior uses fast mode: 100x)",
    )
    replay_parser.add_argument("--max-delay", type=float, help="Maximum delay between events in seconds")
    replay_parser.add_argument("--burst", action="store_true", help="Burst mode: process events as fast as possible")
    replay_parser.add_argument(
        "--dev-mode",
        action="store_true",
        help=(
            "Maximum speed for rapid iteration and smoke tests (1000x + burst). "
            "Use for quick feedback loops, basic functionality testing, "
            "or when you just need the end result fast."
        ),
    )
    replay_parser.add_argument(
        "--fast",
        action="store_true",
        help=(
            "Balanced acceleration for realistic testing (100x + 1s delays). DEFAULT mode. "
            "Use for timing-sensitive apps, integration testing, or when system stability matters."
        ),
    )
    replay_parser.add_argument(
        "--exact",
        action="store_true",
        help=(
            "Preserve original timing exactly (1x speed). "
            "Use when you need to reproduce exact timing behavior or debug timing-dependent issues."
        ),
    )
    replay_parser.add_argument("--no-verify", action="store_true", help="Skip integrity verification")
    replay_parser.add_argument(
        "--skip-unreadable", action="store_true", help="Skip creating files that were unreadable during recording"
    )

    # Info command
    info_parser = subparsers.add_parser("info", help="Show recording information")
    info_parser.add_argument("recording", help="Recording file to analyze (.tar.gz or legacy .json)")

    args = parser.parse_args()

    if args.command == "record":
        recorder = EPURecorder(
            args.directory,
            args.output,
            args.skip_binary_content,
            args.force_text_extensions,
            args.force_binary_extensions,
        )

        # Print binary content handling info
        if args.skip_binary_content:
            print("Binary content handling: Skip binary files (replace with placeholders)")
            if args.force_text_extensions:
                print(f"Force text extensions: {', '.join(args.force_text_extensions)}")
            if args.force_binary_extensions:
                print(f"Force binary extensions: {', '.join(args.force_binary_extensions)}")
        else:
            print("Binary content handling: Store full content of all files")

        # Handle Ctrl+C gracefully
        def signal_handler(sig, frame):
            recorder.stop_recording()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        recorder.start_recording()

    elif args.command == "replay":
        replayer = EPUReplayer(args.recording, args.target)

        # Handle preset modes
        if args.dev_mode:
            print("Development mode: maximum acceleration for fast testing")
            replayer.replay(
                speed_multiplier=1000.0,
                verify_integrity=not args.no_verify,
                max_delay=0.1,
                burst_mode=True,
                skip_unreadable=args.skip_unreadable,
            )
        elif args.fast:
            print("Fast mode: 100x speed with reasonable delays")
            replayer.replay(
                speed_multiplier=100.0,
                verify_integrity=not args.no_verify,
                max_delay=1.0,
                burst_mode=False,
                skip_unreadable=args.skip_unreadable,
            )
        elif args.exact:
            print("Exact mode: preserving original timing")
            replayer.replay(
                speed_multiplier=1.0,
                verify_integrity=not args.no_verify,
                max_delay=None,
                burst_mode=False,
                skip_unreadable=args.skip_unreadable,
            )
        else:
            # Check if user specified custom settings
            has_custom_settings = args.speed != 1.0 or args.max_delay is not None or args.burst

            if has_custom_settings:
                # User specified custom settings - use them
                print(f"Custom mode: {args.speed}x speed")
                replayer.replay(
                    speed_multiplier=args.speed,
                    verify_integrity=not args.no_verify,
                    max_delay=args.max_delay,
                    burst_mode=args.burst,
                    skip_unreadable=args.skip_unreadable,
                )
            else:
                # No preset or custom settings specified - default to fast mode
                print("Fast mode (default): 100x speed with reasonable delays")
                replayer.replay(
                    speed_multiplier=100.0,
                    verify_integrity=not args.no_verify,
                    max_delay=1.0,
                    burst_mode=False,
                    skip_unreadable=args.skip_unreadable,
                )

    elif args.command == "info":
        if not Path(args.recording).exists():
            print(f"Recording file not found: {args.recording}")
            sys.exit(1)

        # Load recording data
        recording_path = Path(args.recording)

        if recording_path.suffix.lower() == ".gz" or tarfile.is_tarfile(recording_path):
            # Load from tar.gz archive
            with tempfile.TemporaryDirectory(prefix="fsinfo_") as temp_dir:
                temp_path = Path(temp_dir)
                with tarfile.open(recording_path, "r:gz") as tar:
                    tar.extractall(temp_path)

                recording_file = temp_path / "recording.json"
                if not recording_file.exists():
                    print("Invalid archive: missing recording.json")
                    sys.exit(1)

                data = json.loads(recording_file.read_text())

                # Count binary chunks
                chunks_dir = temp_path / "chunks"
                chunk_count = len(list(chunks_dir.glob("*.bin"))) if chunks_dir.exists() else 0
        else:
            # Legacy JSON format
            data = json.loads(recording_path.read_text())
            chunk_count = 0

        metadata = data["metadata"]
        events = data["events"]

        print("Recording Information:")
        print(f"  File: {args.recording}")
        print(f"  Recorded from: {metadata['watch_dir']}")
        print(f"  Recorded at: {metadata['recorded_at']}")
        print(f"  Total events: {metadata['total_events']}")
        print(f"  Format version: {metadata.get('version', '1.0')}")
        print(f"  Source platform: {metadata.get('platform', 'unknown')}")
        if chunk_count > 0:
            print(f"  Binary chunks: {chunk_count}")

        # Event type breakdown
        event_types = {}
        for event in events:
            event_type = event["event_type"]
            event_types[event_type] = event_types.get(event_type, 0) + 1

        print("  Event breakdown:")
        for event_type, count in sorted(event_types.items()):
            print(f"    {event_type}: {count}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
