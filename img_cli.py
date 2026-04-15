"""Simple image conversion CLI with optional background removal."""

from __future__ import annotations

import argparse
import io
import os
import sys
from functools import lru_cache
from typing import Callable

from PIL import Image
from tqdm import tqdm

DEFAULT_REMBG_MODEL = "isnet-general-use"
DEFAULT_JPEG_QUALITY = 95
DEFAULT_PNG_COMPRESS_LEVEL = 6


def _normalize_format(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().upper()
    if normalized == "JPG":
        return "JPEG"
    return normalized


def supported_formats() -> list[str]:
    formats = {fmt.upper() for fmt in Image.registered_extensions().values() if fmt}
    return sorted(formats)


def infer_output_format(output_path: str, explicit_output_format: str | None = None) -> str:
    normalized = _normalize_format(explicit_output_format)
    if normalized:
        return normalized

    extension = os.path.splitext(output_path)[1].lower()
    if not extension:
        raise ValueError("Could not infer output format from output file extension. Use --output-format.")

    ext_map = Image.registered_extensions()
    inferred = ext_map.get(extension)
    if not inferred:
        raise ValueError(f"Unsupported output extension '{extension}'. Use --output-format.")

    return _normalize_format(inferred) or inferred


def detect_input_format(input_path: str) -> str | None:
    with Image.open(input_path) as image:
        return _normalize_format(image.format)


@lru_cache(maxsize=1)
def _get_rembg_session(model_name: str = DEFAULT_REMBG_MODEL):
    from rembg import new_session

    return new_session(model_name=model_name)


def _default_remover(image_bytes: bytes, model_name: str = DEFAULT_REMBG_MODEL) -> bytes:
    from rembg import remove

    return remove(image_bytes, session=_get_rembg_session(model_name))


def convert_image(
    input_path: str,
    output_path: str,
    *,
    input_format: str | None = None,
    output_format: str | None = None,
    remove_background: bool = False,
    rembg_model: str = DEFAULT_REMBG_MODEL,
    show_progress: bool = True,
    remover: Callable[[bytes], bytes] | None = None,
) -> None:
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    normalized_expected_input = _normalize_format(input_format)
    detected_format = detect_input_format(input_path)
    if normalized_expected_input and detected_format != normalized_expected_input:
        raise ValueError(
            f"Input format mismatch: expected {normalized_expected_input}, detected {detected_format}."
        )

    resolved_output_format = infer_output_format(output_path, output_format)

    progress_steps = 2 + int(remove_background)
    progress: tqdm | None
    if show_progress:
        progress = tqdm(total=progress_steps, desc="Processing image", unit="step")
    else:
        progress = None

    try:
        with open(input_path, "rb") as file_handle:
            image_bytes = file_handle.read()
        if progress is not None:
            progress.update(1)

        if remove_background:
            image_remover = remover or (lambda value: _default_remover(value, rembg_model))
            image_bytes = image_remover(image_bytes)
            if progress is not None:
                progress.update(1)

        with Image.open(io.BytesIO(image_bytes)) as image:
            save_kwargs = {}
            if resolved_output_format == "JPEG":
                image = image.convert("RGB")
                save_kwargs = {"quality": DEFAULT_JPEG_QUALITY, "optimize": True, "progressive": True}
            elif resolved_output_format == "PNG":
                save_kwargs = {"optimize": True, "compress_level": DEFAULT_PNG_COMPRESS_LEVEL}

            image.save(output_path, format=resolved_output_format, **save_kwargs)

        if progress is not None:
            progress.update(1)
    finally:
        if progress is not None:
            progress.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="img-cli",
        description="Convert image formats and optionally remove backgrounds.",
    )
    parser.add_argument("-i", "--input", help="Input image path")
    parser.add_argument("-o", "--output", help="Output image path")
    parser.add_argument("--input-format", help="Expected input format (e.g. PNG, JPEG, WEBP)")
    parser.add_argument("--output-format", help="Output format (e.g. PNG, JPEG, WEBP)")
    parser.add_argument(
        "--remove-background",
        action="store_true",
        help="Enable background removal mode using rembg.",
    )
    parser.add_argument(
        "--rembg-model",
        default=DEFAULT_REMBG_MODEL,
        help="rembg model name for background removal (default: isnet-general-use).",
    )
    parser.add_argument(
        "--list-formats",
        action="store_true",
        help="List all image formats available via Pillow in this environment.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_formats:
        print("\n".join(supported_formats()))
        return 0

    if not args.input or not args.output:
        parser.error("the following arguments are required: -i/--input and -o/--output")

    try:
        convert_image(
            args.input,
            args.output,
            input_format=args.input_format,
            output_format=args.output_format,
            remove_background=args.remove_background,
            rembg_model=args.rembg_model,
        )
    except ModuleNotFoundError as exc:
        if args.remove_background and exc.name == "rembg":
            print(
                "Background removal requires 'rembg'. Install dependencies from requirements.txt and retry.",
                file=sys.stderr,
            )
            return 1
        raise
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
