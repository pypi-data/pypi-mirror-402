"""Command-line interface for sbx-whisper-cli."""

import argparse
import json
import typing as t

from sbx_whisper_import.hf_whisper_importer import HFWhisperImporter, TranscribeResult


def main() -> None:
    """Run sbx-whisper-import as cli."""
    res = _run_transcription()
    print(json.dumps(res, ensure_ascii=False))  # noqa: T201


def _run_transcription(argv: t.Sequence[str] | None = None) -> TranscribeResult:
    parser = _build_cli()

    args = parser.parse_args(argv)

    importer = HFWhisperImporter(
        model_size=args.model_size, model_verbosity=args.verbosity, verbose=not args.quiet, temperature=args.temperature
    )

    return importer.transcribe(args.input)


def _build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Transcribe audio file with KB-Whisper. Output is in JSON.")
    parser.add_argument("--model-size", type=str, default="small", help="set the size of the model")
    parser.add_argument("--verbosity", type=str, default="standard", help="set the verbosity of the model")
    parser.add_argument(
        "--temperature",
        type=float,
        default=0,
        help="set temperature controlling randomness, values between 0 and 1, defaults to 0",
    )
    parser.add_argument(
        "input", type=str, help="audio input to trancribe in one of the formats MP3, OGG or WAV", metavar="INPUT"
    )
    parser.add_argument("-q", "--quiet", action="store_true", help="Silence output", default=False)
    return parser


if __name__ == "__main__":
    main()
