from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Optional, Tuple

from yt_dlp import YoutubeDL


def _ensure_ffmpeg() -> None:
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg not found on PATH. Install ffmpeg and try again.")


def convert_youtube_to_mp3(url: str, output_dir: Path) -> Tuple[Path, Optional[str], str]:
    _ensure_ffmpeg()
    output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": str(tmp_path / "%(id)s.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_id = info.get("id")
            title = info.get("title")
            input_path = Path(ydl.prepare_filename(info))

        if not video_id:
            raise RuntimeError("Could not determine video id.")

        mp3_path = input_path.with_suffix(".mp3")
        if not mp3_path.exists():
            raise RuntimeError("MP3 conversion failed.")

        final_path = output_dir / f"{video_id}.mp3"
        shutil.move(str(mp3_path), final_path)

    return final_path, title, video_id
