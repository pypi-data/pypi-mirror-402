from gold_dl.handlers.PlaylistHandler import PlaylistHandler
import os
import sys
import json
import asyncio
from typing import Optional
import re
import aiohttp
import time
import subprocess
from concurrent.futures import ThreadPoolExecutor

from pytubefix import YouTube
from pytubefix.helpers import safe_filename

from gold_dl.utils import asking_video_or_audio, console, error_console
from gold_dl.services.AudioService import AudioService
from gold_dl.services.VideoService import VideoService
from gold_dl.services.FileService import FileService
















# =========================
DEFAULT_OUTTMPL = "downloads/%(id)s.%(ext)s"
DEFAULT_THUMBNAIL_TMPL = "downloads/%(id)s.jpg"
DEFAULT_METADATA_TMPL = "downloads/%(id)s.json"

VALID_KEYS = {"id", "ext"}







EXECUTOR = ThreadPoolExecutor(max_workers=6)

_DOWNLOAD_LOCKS: dict[str, asyncio.Lock] = {}
_STREAM_CACHE: dict[str, str] = {}   # key -> file_path






# ===================================
# Global caches and locks
# ===================================
_STREAM_URL_CACHE = {}   #
_CACHE_DURATION = 4 * 60 * 60  



class DownloadService:
    __slots__ = (
        "url", "quality", "is_audio",
        "thumbnail_only", "download_thumbnail_enabled", "export_metadata",
        "path", "thumbnail_path", "metadata_path",
        "video_service", "audio_service", "file_service"
    )

    def __init__(
        self,
        url: str,
        path: Optional[str] = None,
        quality: str = "360p",
        is_audio: bool = False,
        download_thumbnail: Optional[bool] = None,
        thumbnail_only: Optional[bool] = None,
        export_metadata: Optional[bool] = None,
        thumbnail_path: Optional[str] = None,
        metadata_path: Optional[str] = None,
    ):
        self.url = url
        self.quality = quality
        self.is_audio = is_audio

        self.thumbnail_only = bool(thumbnail_only)
        self.download_thumbnail_enabled = bool(download_thumbnail or thumbnail_only)
        self.export_metadata = bool(export_metadata)

        self.path = path or DEFAULT_OUTTMPL
        self.thumbnail_path = thumbnail_path or DEFAULT_THUMBNAIL_TMPL
        self.metadata_path = metadata_path or DEFAULT_METADATA_TMPL

        self.video_service = VideoService(url, quality, "")
        self.audio_service = AudioService(url)
        self.file_service = FileService()

    # =========================
    # Helpers
    # =========================
    @staticmethod
    def _validate_outtmpl(path: str) -> bool:
        return set(re.findall(r"%\((.*?)\)s", path)).issubset(VALID_KEYS)

    @staticmethod
    def _ensure_dir(path: str):
        os.makedirs(path, exist_ok=True)

    def _build_path(self, tmpl: str, video_id: str, ext: str) -> str:
        if not self._validate_outtmpl(tmpl):
            tmpl = DEFAULT_OUTTMPL
        path = tmpl % {"id": video_id, "ext": ext}
        self._ensure_dir(os.path.dirname(path) or ".")
        return path

    # =========================
    # Metadata
    # =========================
    def export_video_metadata(self, video) -> Optional[str]:
        path = self._build_path(self.metadata_path, video.video_id, "json")
        if os.path.exists(path):
            return path
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "id": video.video_id,
                "title": video.title,
                "author": video.author,
                "length": video.length,
                "views": video.views,
                "url": video.watch_url,
                "thumbnail": video.thumbnail_url,
            }, f, ensure_ascii=False, indent=2)
        return path

    # =========================
    # Thumbnail (Async)
    # =========================
    async def download_thumbnail_async(self, video) -> Optional[str]:
        if not video.thumbnail_url:
            return None
        path = self._build_path(self.thumbnail_path, video.video_id, "jpg")
        if os.path.exists(path):
            return path
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(video.thumbnail_url, timeout=8) as r:
                    if r.status != 200:
                        return None
                    with open(path, "wb") as f:
                        f.write(await r.read())
            return path
        except Exception:
            return None

    # =========================
    # Core Download (stream-friendly)
    # =========================
    def _save_stream(self, stream, video_id: str, ext: str) -> str:
        final_path = self._build_path(self.path, video_id, ext)
        if os.path.exists(final_path):
            return final_path

        if getattr(stream, "type", None) == "audio" or not hasattr(stream, "request"):
            self.file_service.save_file(stream, os.path.basename(final_path), os.path.dirname(final_path))
            return final_path

        # تحميل chunk-by-chunk
        with open(final_path, "wb") as f:
            for chunk in stream.request.stream(chunk_size=1024*1024):
                f.write(chunk)
                f.flush()
        return final_path

    # =========================
    # ffmpeg مباشر
    # =========================
    @staticmethod
    def ffmpeg_stream(path: str, output_format="pipe:1"):
        if not os.path.exists(path):
            raise FileNotFoundError(path)
        cmd = [
            "ffmpeg",
            "-re",
            "-i", path,
            "-c", "copy",
            "-f", output_format
        ]
        return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    # =========================
    # Main Download
    # =========================
    def download(self) -> Optional[str]:
        video = self.video_service.search_process()
        video_id = video.video_id

        cache_key = f"{video_id}:{self.is_audio}:{self.quality}"
        if cache_key in _STREAM_CACHE:
            return _STREAM_CACHE[cache_key]

        video_stream, audio_stream, self.quality = self.video_service.get_selected_stream(video, self.is_audio)

        if self.export_metadata:
            self.export_video_metadata(video)

        if self.thumbnail_only:
            return asyncio.run(self.download_thumbnail_async(video))

        if self.download_thumbnail_enabled:
            asyncio.run(self.download_thumbnail_async(video))

        if self.is_audio and audio_stream:
            path = self._save_stream(audio_stream, video_id, "m4a")
        elif video_stream:
            path = self._save_stream(video_stream, video_id, video_stream.subtype or "mp4")
        else:
            return None

        _STREAM_CACHE[cache_key] = path
        return path

    # =========================
    # Direct Stream URL with 4h cache
    # =========================
    def get_stream_url(self) -> Optional[str]:
        """
        رابط مباشر للفيديو أو الصوت بدون تحميل الملف
        مع كاش لمدة 4 ساعات
        """
        video = self.video_service.search_process()
        video_id = video.video_id
        cache_key = f"{video_id}:{self.is_audio}:{self.quality}"

        # تحقق من الكاش
        cached = _STREAM_URL_CACHE.get(cache_key)
        now = time.time()
        if cached:
            ts, url = cached
            if now - ts < _CACHE_DURATION:
                return url  # استخدم الرابط من الكاش

        # الحصول على الرابط الجديد
        video_stream, audio_stream, self.quality = self.video_service.get_selected_stream(video, self.is_audio)
        stream = audio_stream if self.is_audio else video_stream
        if not stream:
            return None

        url = getattr(stream, "url", None)
        if url:
            _STREAM_URL_CACHE[cache_key] = (now, url)
        return url

    async def get_stream_url_async(self) -> Optional[str]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(EXECUTOR, self.get_stream_url)

    # =========================
    # Async Entry
    # =========================
    async def download_async(self) -> Optional[str]:
        lock = _DOWNLOAD_LOCKS.setdefault(self.url, asyncio.Lock())
        async with lock:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(EXECUTOR, self.download)
        
        


class DownloadServicee:
    def __init__(
        self,
        url: str,
        path: str,
        quality: str,
        is_audio: bool = False,
        make_playlist_in_order: bool = False,
    ):
        self.url = url
        self.path = path
        self.quality = quality
        self.is_audio = is_audio
        self.make_playlist_in_order = make_playlist_in_order

        self.video_service = VideoService(self.url, self.quality, self.path)
        self.audio_service = AudioService(url)
        self.file_service = FileService()

    # =========================
    # Helpers
    # =========================
    def _filename_from_stream(self, stream, video_id: str) -> str:
        try:
            ext = "m4a" if stream.type == "audio" else (stream.subtype or "mp4")
        except Exception:
            ext = "m4a" if self.is_audio else "mp4"

        return f"{video_id}.{ext}"

    def _already_downloaded(self, filename: str) -> bool:
        return os.path.exists(os.path.join(self.path, filename))

    # =========================
    # Main download (sync)
    # =========================
    def download(self, title_number: int = 0) -> Optional[str]:
        video, video_id, video_stream, audio_stream, self.quality = self.download_preparing()

        if self.is_audio:
            return self.download_audio(video, audio_stream, video_id)

        return self.download_video(video, video_id, video_stream)

    # =========================
    # Audio
    # =========================
    def download_audio(
        self,
        video: YouTube,
        audio_stream,
        video_id: str,
        title_number: int = 0,
    ) -> Optional[str]:

        if not audio_stream:
            return None

        audio_filename = self._filename_from_stream(audio_stream, video_id)
        final_path = os.path.join(self.path, audio_filename)

        if self._already_downloaded(audio_filename):
            console.print("⏭ Audio already exists, skipping", style="warning")
            return final_path

        try:
            console.print("⏳ Downloading audio...", style="info")
            self.file_service.save_file(audio_stream, audio_filename, self.path)
            return final_path

        except Exception as error:
            error_console.print(
                f"❗ Audio download failed:\n{error}"
            )
            raise RuntimeError(f"Audio download failed: {error}")

    # =========================
    # Video (بدون صوت)
    # =========================
    def download_video(
        self,
        video: YouTube,
        video_id: str,
        video_stream,
        title_number: int = 0,
    ) -> Optional[str]:

        if not video_stream:
            return None

        video_filename = self._filename_from_stream(video_stream, video_id)
        final_path = os.path.join(self.path, video_filename)

        if self._already_downloaded(video_filename):
            console.print("⏭ Video already exists, skipping", style="warning")
            return final_path

        try:
            console.print("⏳ Downloading video...", style="info")
            self.file_service.save_file(video_stream, video_filename, self.path)
            console.print("✅ Video download completed", style="success")
            return final_path

        except Exception as error:
            error_console.print(f"❗ Video download failed:\n{error}")
            raise RuntimeError(f"Video download failed: {error}")

    # =========================
    # Direct Stream URL
    # =========================
    def get_stream_url(self) -> Optional[str]:
        video, video_id, video_stream, audio_stream, self.quality = self.download_preparing()

        stream = audio_stream if self.is_audio else video_stream
        if not stream:
            return None

        return stream.url

    async def get_stream_url_async(self) -> Optional[str]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.get_stream_url)

    # =========================
    # Async Support (Download)
    # =========================
    def _download_sync_return_path(self) -> Optional[str]:
        video, video_id, video_stream, audio_stream, self.quality = self.download_preparing()

        if self.is_audio:
            return self.download_audio(video, audio_stream, video_id)

        return self.download_video(video, video_id, video_stream)

    async def download_async(self) -> Optional[str]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._download_sync_return_path)

    # =========================
    # Playlist
    # =========================
    def get_playlist_links(self):
        handler = PlaylistHandler(self.url, self.path)
        new_path, is_audio, videos_selected, make_in_order, playlist_videos = (
            handler.process_playlist()
        )

        self.make_playlist_in_order = make_in_order

        last_quality = None
        for index, video_id in enumerate(videos_selected):
            self.url = f"https://www.youtube.com/watch?v={video_id}"
            self.path = new_path
            self.is_audio = is_audio
            self.video_service = VideoService(self.url, self.quality, self.path)

            if index == 0:
                last_quality = self.download()
            else:
                self.quality = last_quality
                self.download()

    # =========================
    # Preparing
    # =========================
    def download_preparing(self):
        video = self.video_service.search_process()
        console.print(f"Title: {video.title}\n", style="info")

        video_id = video.video_id
        video_stream, audio_stream, self.quality = (
            self.video_service.get_selected_stream(video, self.is_audio)
        )

        return video, video_id, video_stream, audio_stream, self.quality