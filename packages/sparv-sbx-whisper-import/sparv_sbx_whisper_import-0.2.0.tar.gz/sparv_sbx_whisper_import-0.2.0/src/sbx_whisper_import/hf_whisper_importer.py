"""Whisper importer using transformers."""

import logging
import typing as t

import sparv.api as sparv_api

logger = sparv_api.get_logger(__name__)


class TranscribeChunk(t.TypedDict):
    """Chunked text with timestamp (start, end)."""

    timestamp: tuple[float, float]
    text: str


class TranscribeResult(t.TypedDict):
    """Result from transcribe."""

    text: str
    chunks: list[TranscribeChunk]


class _ModelInfo(t.TypedDict):
    name: str
    revision: str


_SIZE_TO_MODEL_NAME: dict[str, dict[str, _ModelInfo]] = {
    "tiny": {
        "subtitle": {"name": "KBLab/kb-whisper-tiny", "revision": "238d279d9821c32b905fcaff6ce9dad38ad00ab7"},
        "standard": {"name": "KBLab/kb-whisper-tiny", "revision": "e2bca57c3eee6144b9fefd07749580034cfa9686"},
        "strict": {"name": "KBLab/kb-whisper-tiny", "revision": "ea2a872f41f543aaadea23e185e974d1ab29ba2b"},
    },
    "base": {
        "subtitle": {"name": "KBLab/kb-whisper-base", "revision": "7a57b541ccf4aebef73ecfdc064ef4b5cab3b02e"},
        "standard": {"name": "KBLab/kb-whisper-base", "revision": "1ee0facc30bb1f26492bb1360a99d552e25a31c2"},
        "strict": {"name": "KBLab/kb-whisper-base", "revision": "be19431a3fb78b71ac1525bcafe792220b314c9e"},
    },
    "small": {
        "subtitle": {"name": "KBLab/kb-whisper-small", "revision": "8d49820338edb72829d1c44fa70a2ba94a4a20fa"},
        "standard": {"name": "KBLab/kb-whisper-small", "revision": "728c681653e2732ff64618e7f607f509ec87472a"},
        "strict": {"name": "KBLab/kb-whisper-small", "revision": "066ef166dd25b4b27039517ca77af30c1c10688a"},
    },
    "medium": {
        # "subtitle": {"name": "KBLab/kb-whisper-medium", "revision": ""}, NOTE: subtitle not present for medium
        "standard": {"name": "KBLab/kb-whisper-medium", "revision": "32529a74c6662479625746edce7f16fe743fe011"},
        "strict": {"name": "KBLab/kb-whisper-medium", "revision": "51990d2cd5d0cf120b3eceb812bc5407a171a220"},
    },
    "large": {
        "subtitle": {"name": "KBLab/kb-whisper-large", "revision": "50b62f493fa513926007d388f76cce9659bce123"},
        "standard": {"name": "KBLab/kb-whisper-large", "revision": "9e03cd21c14d02c57c33ae90b5803b54995ff241"},
        "strict": {"name": "KBLab/kb-whisper-large", "revision": "ea0a8ac1cda8eab8777bf8d74440eb7606825d8f"},
    },
}


class HFWhisperImporter:
    """Huggingface whisper importer."""

    def __init__(
        self, *, model_size: str, model_verbosity: str = "default", verbose: bool = False, temperature: float = 0
    ) -> None:
        """Huggingface importer using whisper.

        Args:
            model_size: size of the model to use.
            model_verbosity: verbosity of the model.
            verbose: if True more info is written.
            temperature: temperature to control randomness
        """
        import torch  # noqa: PLC0415
        from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline  # noqa: PLC0415
        from transformers.pipelines import AutomaticSpeechRecognitionPipeline  # noqa: PLC0415

        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        if device == "cpu":
            logger.warning("Device is set to use cpu")
        else:
            logger.info("Device is set to use gpu")
        dtype = torch.float16 if torch.cuda.is_available() else torch.float32

        model_verbosity_map = _SIZE_TO_MODEL_NAME.get(model_size.lower())
        if not model_verbosity_map:
            raise ValueError(f"Unknown model_size='{model_size}'.")
        model_info = model_verbosity_map.get(model_verbosity.lower() if model_verbosity != "default" else "standard")
        if not model_info:
            raise ValueError(f"Unsupported model_verbosity='{model_verbosity}' for model_size='{model_size}'.")

        _configure_third_party_loggers(show_progress=verbose)

        model = AutoModelForSpeechSeq2Seq.from_pretrained(
            model_info["name"],
            revision=model_info["revision"],
            dtype=dtype,
            low_cpu_mem_usage=True,
            use_safetensors=True,
        )
        model.to(device)
        processor = AutoProcessor.from_pretrained(model_info["name"], revision=model_info["revision"])

        pipe = pipeline(
            "automatic-speech-recognition",
            model=model,
            tokenizer=processor.tokenizer,
            feature_extractor=processor.feature_extractor,
            dtype=dtype,
            device=device,
            ignore_warning=not verbose,
        )

        generate_kwargs = {"task": "transcribe", "language": "sv", "temperature": temperature}

        self._pipe: AutomaticSpeechRecognitionPipeline = pipe
        self._generate_kwargs = generate_kwargs

    def transcribe(self, audio_path: str) -> TranscribeResult:
        """Transcribe audio from given path.

        Args:
            audio_path: A path to the audio to transcribe.

        Returns:
            The transcribed text along with chunks.
        """
        return self._pipe(
            audio_path,
            # chunk_length_s=30, FIXME: this is instable
            generate_kwargs=self._generate_kwargs,
            return_timestamps=True,
        )  # type: ignore[return-value]


def _configure_third_party_loggers(*, show_progress: bool = False) -> None:
    from huggingface_hub.utils.tqdm import disable_progress_bars  # noqa: PLC0415

    if not show_progress:
        disable_progress_bars()
    for logger_name in ["transformers", "huggingface_hub"]:
        third_party_logger = logging.getLogger(logger_name)
        third_party_logger.setLevel(logging.ERROR)


if __name__ == "__main__":
    import sys

    importer = HFWhisperImporter(model_size="tiny")
    audio_path = sys.argv[1]

    res = importer.transcribe(audio_path)
    print(res)  # noqa: T201
