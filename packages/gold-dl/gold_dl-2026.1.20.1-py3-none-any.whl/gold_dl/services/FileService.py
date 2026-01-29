import os
import sys
import shutil
from typing import Optional
from pytubefix import YouTube
from pytubefix.helpers import safe_filename
from termcolor import colored

from gold_dl.utils import ask_rename_file, error_console, console











class FileService:
    CHUNK_SIZE = 1024 * 1024  # 1MB

    def save_file(
        self,
        stream,
        filename: str,
        path: str,
        resume: bool = False
    ) -> str:
        """
        Save pytube/pytubefix stream safely:
        - Works with audio-only and video streams
        - Resume support for video streams (if possible)
        - Streaming usable during download (.part)
        """
        os.makedirs(path, exist_ok=True)

        final_path = os.path.join(path, filename)
        temp_path = final_path + ".part"

        # ✅ If audio-only or no request, fallback to normal download
        if not hasattr(stream, "request") or getattr(stream, "type", None) == "audio":
            # Audio-only streams: use built-in download
            if os.path.exists(final_path):
                return final_path
            stream.download(output_path=path, filename=filename)
            return final_path

        # ⚡ Video streams (or streams with request attribute)
        downloaded_bytes = 0
        if resume and os.path.exists(temp_path):
            downloaded_bytes = os.path.getsize(temp_path)

        with open(temp_path, "ab") as f:
            for chunk in self._iter_chunks(stream, downloaded_bytes):
                f.write(chunk)
                f.flush()

        # Rename to final file
        os.replace(temp_path, final_path)
        return final_path

    # =========================
    def _iter_chunks(self, stream, start_byte: int = 0):
        """
        Generator yielding chunks for streams with request attribute
        """
        if not hasattr(stream, "request"):
            raise RuntimeError("Unsupported stream type for chunked download")
        return stream.request.stream(
            start_byte=start_byte,
            chunk_size=self.CHUNK_SIZE
        )

    # =========================
    @staticmethod
    def is_file_exists(path: str, filename: str) -> bool:
        return os.path.isfile(os.path.join(path, filename))