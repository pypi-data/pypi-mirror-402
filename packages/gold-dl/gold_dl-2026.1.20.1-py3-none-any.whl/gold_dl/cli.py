"""
gold-dl is a command-line interface, a versatile tool
to download YouTube videos, shorts, and playlists.

This module provides a command-line interface (CLI), a powerful tool designed
to simplify the process of downloading YouTube content directly from the terminal.
gold-dl supports downloading videos (as video or audio), shorts, and playlists,
offering users flexibility and convenience in managing their media downloads.

Usage:
    $ gold-dl download <URL> [options]

Options:
    -a, --audio          Download only audio.
    -f, --footage        Download only video (footage).
    -v, --version        Show the version number.

Example:
    $ gold-dl <YouTube_URL> -a
        Download the audio of the specified YouTube video.

    $ gold-dl <YouTube_URL> -f
        Download the video (footage) of the specified YouTube video.

    $ gold-dl <YouTube_URL>
        Download the file of the specified YouTube video,
        it will ask you about downloading it as video or audio.

    $ gold-dl <YouTube_playlist_URL>
        Download all videos from the specified YouTube playlist.

    $ gold-dl <YouTube_short_URL>
        Download the specified YouTube short video.

Made with ❤️ By Ebraheem. Find me on GitHub: @Hetari. The project lives on @Hetari/gold-dl.

Thank you for using gold-dl! Your support is greatly appreciated. ⭐️
"""

import os
import sys

import typer

from gold_dl.utils import (
    __version__,
    __app__,
    clear,
    error_console,
    console,
    check_internet_connection,
    check_for_updates,
)
from gold_dl.services import DownloadService, DownloadServicee
from gold_dl.handlers import URLHandler

# Create CLI app
app = typer.Typer(
    name="gold-dl",
    add_completion=False,
    help="Awesome CLI to download YouTube videos \
    (as video or audio)/shorts/playlists from the terminal",
    rich_markup_mode="rich",
)


# Define the variables for the arguments and options
url_arg = typer.Argument(
    None,
    help="YouTube URL [red]required[/red]",
    show_default=False
)
path_arg = typer.Argument(
    os.getcwd(),
    help="Path to save video [cyan]default: <current directory>[/cyan]",
    show_default=False
)
audio_option = typer.Option(
    False, "-a", "--audio", help="Download only audio"
)
video_option = typer.Option(
    False, "-f", "--footage", help="Download only video"
)
version_option = typer.Option(
    False, "-v", "--version", help="Show the version number"
)


@app.command(
    name="download",
    help="""
Download YouTube videos (video or audio), shorts, and playlists
using gold-dl.
""",
    epilog="""
Made by VOLT5775

GitHub:
https://github.com/VOLT5775

Project Repository:
https://github.com/VOLT5775/VoLTGoLD-YT

Thank you for using gold-dl
""",
)



def gold_dl(
    url: str = url_arg,
    path: str = path_arg,
    audio: bool = audio_option,
    video: bool = video_option,
    version: bool = version_option
) -> None:
    """
    Downloads a YouTube video.
    """
    from gold_dl.utils import asking_video_or_audio
    
    check_for_updates()

    if version:
        console.print(f"gold-dl {__version__}")
        check_for_updates()
        sys.exit()

    if url is None:
        error_console.print("❗ Missing argument 'URL'.")
        sys.exit()

    clear()

    if not check_internet_connection():
        sys.exit()

    url_handler = URLHandler(url)
    is_valid_link, link_type = url_handler.validate()

    if not is_valid_link:
        sys.exit()

    # 🔊 تحميل صوت
    if audio:
        console.print("[bold cyan]🔊 Audio Mode[/bold cyan]")
        download_service = DownloadServicee(url, path, "best")
        download_service.is_audio = True
        
        # الحصول على المعلومات وتنزيل الصوت
        video_obj, video_id, _, audio_stream, _ = download_service.download_preparing()
        download_service.download_audio(video_obj, audio_stream, video_id)

    # 🎥 تحميل فيديو مباشر (360p) عند -f
    elif video or link_type == "short":
        console.print("[bold cyan]🎥 Video Mode (360p)[/bold cyan]")
        download_service = DownloadServicee(url, path, "360p")
        download_service.is_audio = False
        
        # الحصول على المعلومات وتنزيل الفيديو
        video_obj, video_id, video_stream, _, _ = download_service.download_preparing()
        download_service.download_video(video_obj, video_id, video_stream)

    # 🎬 فيديو عادي (يسأل المستخدم)
    elif link_type == "video":
        # إنشاء خدمة التحميل
        download_service = DownloadServicee(url, path, "360p")
        # استدعاء الوظيفة المعدلة
        asking_video_or_audio(download_service)

    # 📂 قائمة تشغيل
    elif link_type == "playlist":
        # معالجة قائمة التشغيل
        handle_playlist(url, path)

    else:
        error_console.print("❗ Unsupported link type.")
        sys.exit()

    sys.exit()

def handle_playlist(url: str, path: str):
    """معالجة قوائم التشغيل بشكل منفصل"""
    console.print("[bold cyan]📂 Playlist Mode[/bold cyan]")
    
    try:
        # استيراد PlaylistHandler
        from gold_dl.handlers.PlaylistHandler import PlaylistHandler
        
        # إنشاء معالج قائمة التشغيل
        handler = PlaylistHandler(url, path)
        
        # معالجة قائمة التشغيل
        result = handler.process_playlist()
        
        if result is None:
            error_console.print("❗ Playlist processing cancelled or failed")
            return
        
        # فحص النتيجة
        if isinstance(result, tuple) and len(result) >= 5:
            new_path, is_audio, videos_selected, make_in_order, playlist_videos = result
        else:
            error_console.print(f"❗ Unexpected playlist result format: {type(result)}")
            return
        
        if not videos_selected:
            error_console.print("❗ No videos selected from playlist")
            return
        
        console.print(f"📋 Selected {len(videos_selected)} videos from playlist")
        
        # تنزيل كل فيديو
        last_quality = None
        for index, video_id in enumerate(videos_selected, 1):
            console.print(f"\n📥 Downloading {index}/{len(videos_selected)}...")
            
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            if is_audio:
                # تنزيل الصوت
                service = DownloadServicee(video_url, new_path, "best")
                service.is_audio = True
                
                video_obj, video_id, _, audio_stream, _ = service.download_preparing()
                result = service.download_audio(video_obj, audio_stream, video_id)
                
                if result:
                    console.print(f"✅ Audio {index} downloaded")
                else:
                    console.print(f"⚠️  Failed to download audio {index}")
            else:
                # تنزيل الفيديو
                quality_to_use = last_quality if last_quality else "360p"
                service = DownloadServicee(video_url, new_path, quality_to_use)
                service.is_audio = False
                
                video_obj, video_id, video_stream, _, actual_quality = service.download_preparing()
                result = service.download_video(video_obj, video_id, video_stream)
                
                if result:
                    console.print(f"✅ Video {index} downloaded ({actual_quality})")
                    last_quality = actual_quality  # حفظ الجودة للأرقام التالية
                else:
                    console.print(f"⚠️  Failed to download video {index}")
        
        console.print(f"\n🎉 Playlist download completed!", style="success")
        
    except KeyboardInterrupt:
        console.print("\n👋 Playlist download cancelled", style="warning")
    except Exception as e:
        error_console.print(f"❗ Playlist error: {e}")