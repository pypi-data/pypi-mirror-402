import os
import sys

from yaspin import yaspin
from yaspin.spinners import Spinners
from pytubefix import YouTube
from pytubefix.cli import on_progress
from termcolor import colored
from moviepy.video.io.ffmpeg_tools import ffmpeg_merge_video_audio

from gold_dl.utils import (
    console,
    error_console,
    ask_resolution,
    CANCEL_PREFIX
)








class VideoService:
    def __init__(self, url: str, quality: str = "", path: str = ".") -> None:
        self.url = url
        self.quality = quality  # الآن يمكن أن تكون سلسلة فارغة
        self.path = path

    # =========================
    # Search
    # =========================
    def search_process(self) -> YouTube:
        try:
            video = self.__video_search()
        except Exception as error:
            error_console.print(f"❗ Error: {error}")
            sys.exit(1)

        if not video:
            error_console.print("❗ No stream available for the URL.")
            sys.exit(1)

        return video

    @yaspin(
        text=colored("Searching for the video", "green"),
        color="green",
        spinner=Spinners.point,
    )
    def __video_search(self) -> YouTube:
        return YouTube(
            self.url,
            use_oauth=True,
            allow_oauth_cache=True,
            on_progress_callback=on_progress,
        )

    # =========================
    # Streams (Progressive only)
    # =========================
    def get_available_resolutions(self, video: YouTube):
        progressive_streams = video.streams.filter(progressive=True, file_extension="mp4").order_by("resolution").desc()

        if not progressive_streams:
            error_console.print("❗ No progressive streams (video+audio) found.")
            sys.exit(1)

        resolutions = [s.resolution for s in progressive_streams]
        sizes = [f"{s.filesize / (1024*1024):.2f} MB" for s in progressive_streams]

        return resolutions, sizes, progressive_streams

    def get_selected_stream(self, video: YouTube, requested_quality: str = ""):
        """
        الحصول على تيار الفيديو بالجودة المطلوبة
        
        Args:
            video: كائن YouTube
            requested_quality: الجودة المطلوبة (مثل "720p", "1080p")
                            يمكن أن تكون سلسلة فارغة "" أو None
            
        Returns:
            tuple: (stream, actual_quality)
        """
        # الحصول على جميع التيارات المتاحة
        resolutions, sizes, progressive_streams = self.get_available_resolutions(video)
        
        # إذا لم تكن هناك جودة مطلوبة، نرجع أفضل جودة
        if not requested_quality and not self.quality:
            best_stream = progressive_streams.first()
            return best_stream, best_stream.resolution
        
        # استخدام الجودة المطلوبة أولاً، ثم جودة الكلاس
        quality_to_search = requested_quality or self.quality
        
        # البحث عن الجودة المحددة
        selected_stream = None
        actual_quality = quality_to_search
        
        # إذا كانت الجودة المطلوبة 360p → نبحث عن itag 18 أولاً
        if quality_to_search == "360p":
            itag_18 = video.streams.get_by_itag(18)
            if itag_18:
                selected_stream = itag_18
                actual_quality = "360p"
        
        # إذا لم نجد itag 18، نبحث في التيارات المتاحة
        if not selected_stream:
            for stream in progressive_streams:
                if stream.resolution == quality_to_search:
                    selected_stream = stream
                    actual_quality = quality_to_search
                    break
        
        # إذا لم توجد الجودة المطلوبة، نأخذ أفضل جودة متاحة
        if not selected_stream:
            selected_stream = progressive_streams.first()
            actual_quality = selected_stream.resolution
        
        return selected_stream, actual_quality