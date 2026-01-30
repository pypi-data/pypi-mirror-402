"""Sparv importer for using Whisper."""

from sparv import api as sparv_api
from sparv.api import Config, Output, Source, SourceFilename, SourceStructure, Text

from sbx_whisper_import.hf_whisper_importer import HFWhisperImporter

logger = sparv_api.get_logger(__name__)


@sparv_api.importer(
    "Import audio from MP3 with Whisper",
    file_extension="mp3",
    outputs=["text", "utterance"],
    text_annotation="text",
)
def parse_mp3(
    source_file: SourceFilename = SourceFilename(),
    source_dir: Source = Source(),
    model_size: str = Config("sbx_whisper_import.model_size"),
    model_verbosity: str = Config("sbx_whisper_import.model_verbosity"),
    temperature: float = Config("sbx_whisper_import.temperature"),  # type: ignore[assignment]
) -> None:
    """Transcribe mp3 file as input to Sparv."""
    transcribe_audio(
        source_file=source_file,
        source_dir=source_dir,
        model_size=model_size,
        model_verbosity=model_verbosity,
        extension=".mp3",
        temperature=temperature,
    )


@sparv_api.importer(
    "Import audio from OGG with Whisper",
    file_extension="ogg",
    outputs=["text", "utterance"],
    text_annotation="text",
)
def parse_ogg(
    source_file: SourceFilename = SourceFilename(),
    source_dir: Source = Source(),
    model_size: str = Config("sbx_whisper_import.model_size"),
    model_verbosity: str = Config("sbx_whisper_import.model_verbosity"),
    temperature: float = Config("sbx_whisper_import.temperature"),  # type: ignore[assignment]
) -> None:
    """Transcribe ogg file as input to Sparv."""
    transcribe_audio(
        source_file=source_file,
        source_dir=source_dir,
        model_size=model_size,
        model_verbosity=model_verbosity,
        extension=".ogg",
        temperature=temperature,
    )


@sparv_api.importer(
    "Import audio from WAV with Whisper",
    file_extension="wav",
    outputs=["text", "utterance"],
    text_annotation="text",
)
def parse_wav(
    source_file: SourceFilename = SourceFilename(),
    source_dir: Source = Source(),
    model_size: str = Config("sbx_whisper_import.model_size"),
    model_verbosity: str = Config("sbx_whisper_import.model_verbosity"),
    temperature: float = Config("sbx_whisper_import.temperature"),  # type: ignore[assignment]
) -> None:
    """Transcribe wav file as input to Sparv."""
    transcribe_audio(
        source_file=source_file,
        source_dir=source_dir,
        model_size=model_size,
        model_verbosity=model_verbosity,
        extension=".wav",
        temperature=temperature,
    )


def transcribe_audio(
    source_file: SourceFilename,
    source_dir: Source,
    model_size: str,
    model_verbosity: str,
    temperature: float,
    extension: str,
) -> None:
    """Transcribe audio file as input to Sparv."""
    text, utterance_spans, utterance_starts, utterance_ends = _transcribe_and_prepare_spans(
        model_size, model_verbosity, temperature, str(source_dir.get_path(source_file, extension))
    )

    # Make up a text annotation surrounding the whole file
    text_annotation = [
        "text",
        "text:source_filename",
        "text:model_size",
        "text:model_verbosity",
        "text:temperature",
        "utterance",
        "utterance:start",
        "utterance:end",
    ]
    source_file_name = f"{source_file}{extension}"

    # Write output
    Text(source_file).write(text)
    Output("text", source_file=source_file).write([(0, len(text))])
    Output("text:source_filename", source_file=source_file).write([source_file_name])
    Output("text:model_size", source_file=source_file).write([model_size])
    Output("text:model_verbosity", source_file=source_file).write([model_verbosity])
    Output("text:temperature", source_file=source_file).write([temperature])
    Output("utterance", source_file=source_file).write(utterance_spans)
    Output("utterance:start", source_file=source_file).write(utterance_starts)
    Output("utterance:end", source_file=source_file).write(utterance_ends)
    SourceStructure(source_file).write(text_annotation)


def _transcribe_and_prepare_spans(
    model_size: str, model_verbosity: str, temperature: float, source_filename: str
) -> tuple[str, list[tuple[int, int]], list[float], list[float]]:
    importer = HFWhisperImporter(model_size=model_size, model_verbosity=model_verbosity, temperature=temperature)

    res = importer.transcribe(source_filename)

    logger.debug("res=%s", res)

    utterance_spans: list[tuple[int, int]] = []
    utterance_starts: list[float] = []
    utterance_ends: list[float] = []
    curr_start: int = 0
    curr_end: int = 0
    for chunk in res["chunks"]:
        utterance_starts.append(chunk["timestamp"][0])
        utterance_ends.append(chunk["timestamp"][1])
        curr_end += len(chunk["text"])
        if chunk["text"].startswith(" "):
            curr_start += 1
        logger.debug("chunk='%s' start=%d end=%d", chunk["text"], curr_start, curr_end)
        utterance_spans.append((curr_start, curr_end))
        curr_start = curr_end

    return res["text"], utterance_spans, utterance_starts, utterance_ends
