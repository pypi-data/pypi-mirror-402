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








EXECUTOR = ThreadPoolExecutor(max_workers=6)

_DOWNLOAD_LOCKS: dict[str, asyncio.Lock] = {}
_STREAM_CACHE: dict[str, str] = {}   # key -> file_path






# ===================================
# Global caches and locks
# ===================================
_STREAM_URL_CACHE = {}   #
_CACHE_DURATION = 4 * 60 * 60  





# الثوابت الافتراضية
DEFAULT_OUTTMPL = "downloads/%(id)s.%(ext)s"
DEFAULT_THUMBNAIL_TMPL = "downloads/%(id)s.jpg"
DEFAULT_METADATA_TMPL = "downloads/%(id)s.json"
VALID_KEYS = {"id", "ext", "title", "author"}





class DownloadService:
    __slots__ = (
        "url", "quality", "is_audio",
        "thumbnail_only", "download_thumbnail_enabled", "_export_metadata",
        "path", "thumbnail_path", "metadata_path",
        "video_service", "audio_service", "file_service"
    )

    def __init__(
        self,
        url: str,
        path: Optional[str] = None,
        quality: Optional[str] = None,
        is_audio: Optional[bool] = None,
        download_thumbnail: Optional[bool] = False,
        thumbnail_only: Optional[bool] = False,
        export_metadata: Optional[bool] = False,
        thumbnail_path: Optional[str] = None,
        metadata_path: Optional[str] = None,
    ):
        self.url = url
        self.is_audio = is_audio
        
        # تحديد الجودة افتراضياً بناءً على النوع
        if quality is None:
            # إذا لم يتم تحديد جودة، نحددها بناءً على النوع
            if is_audio:
                self.quality = "best"  # أفضل جودة للصوت
            else:
                self.quality = "360p"  # جودة افتراضية للفيديو
        else:
            self.quality = quality
            
        self.thumbnail_only = bool(thumbnail_only)
        self.download_thumbnail_enabled = bool(download_thumbnail or thumbnail_only)
        self._export_metadata = bool(export_metadata)  # تغيير الاسم لتجنب التعارض

        self.path = path or DEFAULT_OUTTMPL
        self.thumbnail_path = thumbnail_path or DEFAULT_THUMBNAIL_TMPL
        self.metadata_path = metadata_path or DEFAULT_METADATA_TMPL

        # استخدام الجودة في VideoService
        service_quality = quality if quality else ""
        self.video_service = VideoService(url, service_quality, "")
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
        if not self._export_metadata:
            return None
            
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
    # Core Download
    # =========================
    def _save_stream(self, stream, video_id: str, ext: str) -> str:
        final_path = self._build_path(self.path, video_id, ext)
        if os.path.exists(final_path):
            return final_path

        if getattr(stream, "type", None) == "audio" or not hasattr(stream, "request"):
            self.file_service.save_file(stream, os.path.basename(final_path), os.path.dirname(final_path))
            return final_path

        with open(final_path, "wb") as f:
            for chunk in stream.request.stream(chunk_size=1024*1024):
                f.write(chunk)
                f.flush()
        return final_path

    # =========================
    # Download Methods
    # =========================
    def download_video(self, quality: Optional[str] = None) -> Optional[str]:
        """تنزيل الفيديو"""
        video = self.video_service.search_process()
        video_id = video.video_id
        q = quality or self.quality
        stream, actual_quality = self.video_service.get_selected_stream(video, requested_quality=q)
        if not stream:
            return None
        
        if self._export_metadata:
            self.export_video_metadata(video)
            
        return self._save_stream(stream, video_id, stream.subtype or "mp4")

    def download_audio(self) -> Optional[str]:
        """تنزيل الصوت فقط باستخدام AudioService"""
        try:
            # الحصول على معلومات الفيديو أولاً
            video = self.video_service.search_process()
            video_id = video.video_id
            
            # استخدام AudioService للحصول على stream الصوت
            audio_stream = self.audio_service.get_audio_streams(video)
            
            if not audio_stream:
                return None
            
            # تحديد امتداد الملف
            if hasattr(audio_stream, 'mime_type'):
                if 'webm' in audio_stream.mime_type:
                    ext = "webm"
                elif 'mp4' in audio_stream.mime_type:
                    ext = "m4a"
                else:
                    ext = "mp3"
            else:
                ext = "mp3"
            
            # تصدير البيانات الوصفية إذا مطلوب
            if self._export_metadata:
                self.export_video_metadata(video)
                
            return self._save_stream(audio_stream, video_id, ext)
            
        except Exception as e:
            print(f"خطأ في download_audio: {e}")
            return None

    async def download_thumbnail(self) -> Optional[str]:
        if not self.download_thumbnail_enabled:
            return None
            
        video = self.video_service.search_process()
        return await self.download_thumbnail_async(video)

    def export_metadata(self) -> Optional[str]:
        """دالة لتصدير البيانات الوصفية"""
        if not self._export_metadata:
            return None
            
        video = self.video_service.search_process()
        return self.export_video_metadata(video)

    def get_direct_url(self, is_audio: bool = False) -> Optional[str]:
        """الحصول على رابط مباشر"""
        try:
            video = self.video_service.search_process()
            
            if is_audio:
                # للصوت: استخدام AudioService
                audio_stream = self.audio_service.get_audio_streams(video)
                if audio_stream and hasattr(audio_stream, 'url'):
                    return audio_stream.url
            else:
                # للفيديو: استخدام VideoService
                stream, _ = self.video_service.get_selected_stream(video, requested_quality=self.quality)
                if stream and hasattr(stream, 'url'):
                    return stream.url
            
            return None
            
        except Exception as e:
            print(f"خطأ في get_direct_url: {e}")
            return None

    def download(self, is_audio: Optional[bool] = None) -> Optional[str]:
        """
        دالة تنزيل ذكية تختار بين الصوت والفيديو
        
        Args:
            is_audio: إذا كان None، يستخدم self.is_audio
                     إذا كان True/False، يستخدم القيمة المحددة
        """
        # تحديد نوع التنزيل
        download_type = is_audio if is_audio is not None else self.is_audio
        
        if download_type:
            return self.download_audio()  # تنزيل الصوت فقط
        else:
            return self.download_video()  # تنزيل الفيديو

    async def download_async(self, is_audio: Optional[bool] = None) -> Optional[str]:
        """نسخة غير متزامنة من دالة التنزيل"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self.download(is_audio))
        
        


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
            if self.is_audio:
                ext = "m4a" if hasattr(stream, 'mime_type') and 'mp4' in stream.mime_type else "mp3"
            else:
                ext = stream.subtype or "mp4"
        except Exception:
            ext = "m4a" if self.is_audio else "mp4"

        return f"{video_id}.{ext}"

    def _already_downloaded(self, filename: str) -> bool:
        return os.path.exists(os.path.join(self.path, filename))

    # =========================
    # Preparing
    # =========================
    def download_preparing(self):
        """إعداد المعلومات قبل التنزيل"""
        video = self.video_service.search_process()
        console.print(f"Title: {video.title}\n", style="info")

        video_id = video.video_id
        
        # تحديد streams حسب النوع
        video_stream = None
        audio_stream = None
        
        if self.is_audio:
            # للحصول على الصوت فقط
            audio_stream = self.audio_service.get_audio_streams(video)
            if audio_stream and self.quality == "best":
                # تحديث الجودة للصوت إذا كانت "best"
                if hasattr(audio_stream, 'abr'):
                    self.quality = audio_stream.abr
        else:
            # للحصول على الفيديو
            video_stream, actual_quality = self.video_service.get_selected_stream(video)
            self.quality = actual_quality  # تحديث الجودة الفعلية

        return video, video_id, video_stream, audio_stream, self.quality

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
            console.print("❌ No audio stream found", style="error")
            return None

        audio_filename = self._filename_from_stream(audio_stream, video_id)
        final_path = os.path.join(self.path, audio_filename)

        if self._already_downloaded(audio_filename):
            console.print("⏭ Audio already exists, skipping", style="warning")
            return final_path

        try:
            console.print("⏳ Downloading audio...", style="info")
            self.file_service.save_file(audio_stream, audio_filename, self.path)
            console.print("✅ Audio download completed", style="success")
            return final_path

        except Exception as error:
            error_console.print(f"❗ Audio download failed:\n{error}")
            return None

    # =========================
    # Video
    # =========================
    def download_video(
        self,
        video: YouTube,
        video_id: str,
        video_stream,
        title_number: int = 0,
    ) -> Optional[str]:

        if not video_stream:
            console.print("❌ No video stream found", style="error")
            return None

        video_filename = self._filename_from_stream(video_stream, video_id)
        final_path = os.path.join(self.path, video_filename)

        if self._already_downloaded(video_filename):
            console.print("⏭ Video already exists, skipping", style="warning")
            return final_path

        try:
            console.print(f"⏳ Downloading video ({self.quality})...", style="info")
            self.file_service.save_file(video_stream, video_filename, self.path)
            console.print("✅ Video download completed", style="success")
            return final_path

        except Exception as error:
            error_console.print(f"❗ Video download failed:\n{error}")
            return None

    # =========================
    # Direct Stream URL
    # =========================
    def get_stream_url(self) -> Optional[str]:
        """الحصول على رابط stream مباشر"""
        video, video_id, video_stream, audio_stream, self.quality = self.download_preparing()

        stream = audio_stream if self.is_audio else video_stream
        if not stream:
            return None

        return stream.url if hasattr(stream, 'url') else None

    async def get_stream_url_async(self) -> Optional[str]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.get_stream_url)

    # =========================
    # Async Support (Download)
    # =========================
    def _download_sync_return_path(self) -> Optional[str]:
        return self.download()

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