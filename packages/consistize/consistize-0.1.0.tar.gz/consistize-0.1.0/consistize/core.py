from __future__ import annotations

import base64
import imghdr
import json
import mimetypes
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Union

from openai import OpenAI

PathLike = Union[str, Path]

DEFAULT_MODEL = "gpt-5.2"
DEFAULT_SYSTEM_PROMPT = (
    "You are an image consistency bot. Your job is to look at a provided image "
    "and confirm the background is consistent with the given reference images. "
    "The background may match one or multiple of the reference images. If you "
    "can't see the entire reference in the background that is okay."
)

DEFAULT_USER_PROMPT = (
    "The first image is the target; the remaining images are references. "
    "Respond only with JSON that matches the schema."
)


@dataclass(frozen=True)
class ConsistencyResult:
    consistency_score: int
    inconsistent_parts: List[str]
    background_fix_prompts: List[str]


class Consistize:
    def __init__(
        self,
        reference_images: Sequence[PathLike],
        *,
        client: Optional[OpenAI] = None,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
    ) -> None:
        if not reference_images:
            raise ValueError("reference_images must contain at least one path.")
        self.reference_images = [Path(p) for p in reference_images]
        self.model = model
        if client is not None:
            self.client = client
        elif api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            if not os.getenv("OPENAI_API_KEY"):
                raise ValueError(
                    "OpenAI API key not found. Set OPENAI_API_KEY or pass api_key "
                    "to Consistize."
                )
            self.client = OpenAI()

    def run(
        self,
        image: PathLike,
        *,
        prompt: Optional[str] = None,
        model: Optional[str] = None,
    ) -> ConsistencyResult:
        response = self.run_raw(image, prompt=prompt, model=model)
        output_text = _extract_output_text(response)
        data = json.loads(output_text)
        return ConsistencyResult(
            consistency_score=int(data["consistency_score"]),
            inconsistent_parts=list(data["inconsistent_parts"]),
            background_fix_prompts=list(data["background_fix_prompts"]),
        )

    def run_raw(
        self,
        image: PathLike,
        *,
        prompt: Optional[str] = None,
        model: Optional[str] = None,
    ):
        target_path = Path(image)
        _ensure_exists(target_path)
        for reference_path in self.reference_images:
            _ensure_exists(reference_path)

        user_content = [
            {"type": "input_text", "text": prompt or DEFAULT_USER_PROMPT},
            {
                "type": "input_image",
                "image_url": _encode_image(target_path),
            },
        ]

        for reference_path in self.reference_images:
            user_content.append(
                {
                    "type": "input_image",
                    "image_url": _encode_image(reference_path),
                }
            )

        return self.client.responses.create(
            model=model or self.model,
            input=[
                {
                    "role": "system",
                    "content": [
                        {"type": "input_text", "text": DEFAULT_SYSTEM_PROMPT}
                    ],
                },
                {"role": "user", "content": user_content},
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "image_consistency_response",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "consistency_score": {
                                "type": "integer",
                                "description": (
                                    "Image consistency score (0 = fully inconsistent, "
                                    "100 = perfectly consistent)."
                                ),
                                "minimum": 0,
                                "maximum": 100,
                            },
                            "inconsistent_parts": {
                                "type": "array",
                                "description": (
                                    "A list of strings describing the inconsistent "
                                    "parts of the image."
                                ),
                                "items": {"type": "string"},
                            },
                            "background_fix_prompts": {
                                "type": "array",
                                "description": (
                                    "A list of prompts to modify the background and fix "
                                    "the inconsistencies in the image."
                                ),
                                "items": {"type": "string"},
                            },
                        },
                        "required": [
                            "consistency_score",
                            "inconsistent_parts",
                            "background_fix_prompts",
                        ],
                        "additionalProperties": False,
                    },
                },
                "verbosity": "medium",
            },
        )


def _ensure_exists(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)
    if not path.is_file():
        raise ValueError(f"Expected a file path, got: {path}")


def _encode_image(path: Path) -> str:
    mime_type = _guess_mime_type(path)
    with path.open("rb") as handle:
        encoded = base64.b64encode(handle.read()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def _guess_mime_type(path: Path) -> str:
    mime_type, _ = mimetypes.guess_type(str(path))
    if mime_type:
        return mime_type
    detected = imghdr.what(path)
    if detected:
        return f"image/{detected}"
    return "application/octet-stream"


def _extract_output_text(response) -> str:
    if getattr(response, "output_text", None):
        return response.output_text

    output = getattr(response, "output", None) or []
    for item in output:
        if getattr(item, "type", None) != "message":
            continue
        for part in getattr(item, "content", []) or []:
            if getattr(part, "type", None) == "output_text":
                return part.text

    raise ValueError("OpenAI response did not contain text output.")
