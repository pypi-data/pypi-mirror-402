import os
import subprocess

from edi_core.utils.assertions import assert_file_exists
from edi_core.utils.file import dir_exists, get_file_name_without_extension


def extract_audio(file_path: str, output_path: str):
    assert_file_exists(file_path)
    result = subprocess.run(
        ['ffmpeg', '-i', file_path, '-q:a', '0', '-map', 'a', output_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to extract audio: {result.stderr.decode()}")


def split_audio(source_file: str, dest_dir: str, seconds: int):
    assert_file_exists(source_file)
    if not dir_exists(dest_dir):
        os.makedirs(dest_dir, exist_ok=True)

    base_name = get_file_name_without_extension(source_file)
    segment_pattern = os.path.join(dest_dir, f"{base_name}_%03d.mp3")

    result = subprocess.run(
        ['ffmpeg', '-i', source_file, '-f', 'segment', '-segment_time', str(seconds), '-c', 'copy', segment_pattern],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    if result.returncode != 0:
        raise RuntimeError(f"Failed to split audio: {result.stderr.decode()}")

    return sorted([os.path.join(dest_dir, f) for f in os.listdir(dest_dir) if f.startswith(base_name)],
                  key=lambda x: x.lower())
