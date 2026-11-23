"""Entrypoint for the make.fun news-image-20261122 entry.

Reads entry.png from the same directory as this file and copies it to
the directory named by MAKEFUN_OUTPUT_DIR (current working directory
if the variable is unset). Standard library only.
"""

import os
import shutil
import struct
import sys
import zlib

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAX_SIZE = 1048576
EXPECTED_WIDTH = 1024
EXPECTED_HEIGHT = 1024


class ValidationError(Exception):
    pass


def validate_png(data):
    """Check the PNG is well-formed and matches the bounty limits.

    Verifies the signature, walks every chunk checking its CRC, requires
    IHDR first with exactly 1024x1024 dimensions, requires at least one
    IDAT chunk and a final IEND chunk, and requires the file to be under
    1 MiB. Raises ValidationError with a clear message on any failure.
    """
    if len(data) < len(PNG_SIGNATURE):
        raise ValidationError("file too small to be a PNG")
    if data[:8] != PNG_SIGNATURE:
        raise ValidationError("bad PNG signature")
    if len(data) >= MAX_SIZE:
        raise ValidationError(
            "file is %d bytes, must be under %d" % (len(data), MAX_SIZE)
        )
    pos = 8
    seen = []
    width = None
    height = None
    first = True
    while True:
        if pos + 8 > len(data):
            raise ValidationError("truncated chunk header at offset %d" % pos)
        length, chunk_type = struct.unpack(">I4s", data[pos:pos + 8])
        chunk_end = pos + 8 + length + 4
        if chunk_end > len(data):
            raise ValidationError("truncated %s chunk" % chunk_type.decode("ascii", "replace"))
        chunk_data = data[pos + 8:pos + 8 + length]
        stored_crc = struct.unpack(">I", data[pos + 8 + length:chunk_end])[0]
        actual_crc = zlib.crc32(chunk_type + chunk_data) & 0xFFFFFFFF
        if actual_crc != stored_crc:
            raise ValidationError(
                "bad CRC in %s chunk" % chunk_type.decode("ascii", "replace")
            )
        name = chunk_type.decode("ascii", "replace")
        seen.append(name)
        if first:
            if chunk_type != b"IHDR":
                raise ValidationError("first chunk is %s, expected IHDR" % name)
            if length != 13:
                raise ValidationError("IHDR length is %d, expected 13" % length)
            width, height = struct.unpack(">II", chunk_data[:8])
            if width != EXPECTED_WIDTH or height != EXPECTED_HEIGHT:
                raise ValidationError(
                    "image is %dx%d, expected %dx%d"
                    % (width, height, EXPECTED_WIDTH, EXPECTED_HEIGHT)
                )
            first = False
        if chunk_type == b"IEND":
            if pos + 12 != len(data):
                raise ValidationError("trailing data after IEND chunk")
            break
        pos = chunk_end
    if "IDAT" not in seen:
        raise ValidationError("no IDAT chunk found")
    if "IEND" not in seen:
        raise ValidationError("no IEND chunk found")


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    source = os.path.join(here, "entry.png")
    try:
        with open(source, "rb") as handle:
            data = handle.read()
    except OSError as exc:
        print("error: cannot read %s: %s" % (source, exc), file=sys.stderr)
        return 1
    try:
        validate_png(data)
    except ValidationError as exc:
        print("error: entry.png failed validation: %s" % exc, file=sys.stderr)
        return 1
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or os.getcwd()
    os.makedirs(out_dir, exist_ok=True)
    destination = os.path.join(out_dir, "entry.png")
    shutil.copyfile(source, destination)
    print("Wrote entry.png to %s" % destination)
    return 0


if __name__ == "__main__":
    sys.exit(main())
