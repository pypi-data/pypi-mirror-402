"""
This module contains the utils functions for the gold-dl package.
"""

import subprocess
import sys
import os

import requests
import inquirer
import questionary
from yaspin import yaspin
from yaspin.spinners import Spinners
from rich.console import Console
from rich.theme import Theme
from termcolor import colored
from pytubefix import __version__ as pytubefix_version


__app__ = "gold-dl"
__version__ = "2026.1.20.2"
ABORTED_PREFIX = "Aborted"
CANCEL_PREFIX = "Cancel"

FORCE_144P = False
# Set up the console
custom_theme = Theme({
    "info": "#64b0f2",
    "warning": "color(3)",
    "success": "green",
})
console = Console(theme=custom_theme)
error_console = Console(stderr=True, style="red")


def clear() -> None:
    """
    Function to clear the console screen, it can be used for any operating system

    Args:
        This function does not take any parameters.

    Returns:
        It does not return anything (None).
    """
    # For Windows
    if os.name == "nt":
        os.system("cls")
    else:
        # For Unix/Linux/MacOS
        os.system("clear")


@yaspin(text="Checking internet connection", color="blue", spinner=Spinners.earth)
def is_internet_available() -> bool:
    """
    Checks if internet connection is available by making a simple request
    to http://www.google.com with a timeout of 5 seconds.

    Returns:
        bool: the request status (True if available, False if not).
    """
    try:
        requests.get("https://www.google.com", timeout=5)
        return True
    except Exception:
        return False


def file_type() -> str:
    """
    Prompts the user to choose a file type for download and returns
    the chosen file type as a string.

    Args:
        None

    Returns:
        str: The chosen file type as a string.
    """
    # make the console font to red
    questions = [
        inquirer.List(
            "file_type",
            message="Choose the file type you want to download",
            choices=['Audio', 'Video', CANCEL_PREFIX],
        ),
    ]

    try:
        answer = inquirer.prompt(questions)["file_type"]

    # TypeError: 'NoneType' object is not subscriptable

    except TypeError:
        return ABORTED_PREFIX

    except Exception as error:
        error_console.print(f"Error: {error}")
        sys.exit()

    return answer


def ask_resolution(resolutions: set, sizes) -> str:
    """
    If FORCE_144P is True:
    - Do NOT ask user
    - Select 144p automatically
    Otherwise:
    - Ask user normally
    """
    if FORCE_144P:
        try:
            available = sorted(
                int(r.replace("p", ""))
                for r in resolutions
                if isinstance(r, str) and r.endswith("p")
            )

            target = 144

            if target in available:
                return "144p"

            lower = [r for r in available if r < target]
            if lower:
                return f"{max(lower)}p"

            return f"{max(available)}p"

        except Exception as error:
            error_console.print(f"Auto resolution error: {error}")
            sys.exit()

    # 🔽 الوضع العادي (يسأل المستخدم)
    size_resolution_mapping = dict(zip(resolutions, sizes))

    resolution_choices = [
        f"{size} ~= {resolution}"
        for size, resolution in size_resolution_mapping.items()
    ] + [CANCEL_PREFIX]

    questions = [
        inquirer.List(
            "resolution",
            message="Choose the resolution you want to download",
            choices=resolution_choices,
        ),
    ]

    try:
        answer = inquirer.prompt(questions)["resolution"]
    except TypeError:
        return ABORTED_PREFIX
    except Exception as error:
        error_console.print(f"Error: {error}")
        sys.exit()

    return answer.split(" ~= ")[0]


def ask_rename_file(filename: str) -> str:
    """
    Function to ask the user whether to rename, overwrite, or cancel the file operation.

    Args:
        filename (str): The name of the file.

    Returns:
        str: The user's choice to rename, overwrite, or cancel the file operation.
    """
    console.print(
        f"'{filename}' is already exists, do you want to:", style="info")
    questions = [
        inquirer.List(
            "rename",
            message="Do you want to",
            choices=['Rename it', 'Overwrite it', CANCEL_PREFIX.capitalize()],
        ),
    ]
    return inquirer.prompt(questions)["rename"]


def ask_playlist_video_names(videos):
    note = colored("NOTE:", "cyan")
    select_one = colored("<space>", "red")
    select_all = colored("<ctrl+a>", "red")
    invert_selection = colored("<ctrl+i>", "red")
    restart_selection = colored("<ctrl+r>", "red")

    print((
        f"{note} Press {select_one} to select the videos, {select_all} to select all, "
        f"{invert_selection} to invert selection, and {restart_selection} to restart selection"
    ))

    questions = [
        inquirer.Checkbox(
            "names",
            message="Choose the videos you want to download",
            choices=videos,
        ),
    ]

    try:
        answer = inquirer.prompt(questions)["names"]

    except TypeError:
        return ABORTED_PREFIX

    except Exception as error:
        error_console.print(f"Error: {error}")
        sys.exit()

    return answer


def ask_for_make_playlist_in_order():
    # make_in_order = colored( "", "cyan")

    questions = [
        inquirer.Confirm(
            "ask_for_make_playlist_in_order",
            message="Do you want to add the number order of the videos (ex: 1, 2, ...etc)? ",
            default=False
        ),
    ]

    try:
        answer = inquirer.prompt(questions)["ask_for_make_playlist_in_order"]

    except TypeError:
        return ABORTED_PREFIX

    except Exception as error:
        error_console.print(f"Error: {error}")
        sys.exit()

    return answer


def check_for_updates() -> None:
    """
    A function to check for updates of a given package or packages.

    Returns:
        None
    """
    libraries = {
        'gold-dl': {
            'version': __version__,
            'repository': 'https://github.com/VOLT5775/VoLTGoLD-YT'
        },
        'pytubefix': {
            'version': pytubefix_version,
            'repository': 'https://github.com/Hetari/pytubefix'
        }
    }

    try:
        for library, version in libraries.items():
            r = requests.get(
                f'https://pypi.org/pypi/{library}/json', headers={'Accept': 'application/json'})
            if r.status_code == 200:
                latest_version = r.json()['info']['version']

                if latest_version != version['version']:
                    console.print(
                        f"👉 A new version of [blue]{library}[/blue] is available: {latest_version} " +
                        f"Updating it now... ",
                        style="warning"
                    )
                    # auto-update the package
                    try:
                        subprocess.check_call(
                            [sys.executable, '-m', 'pip', 'install', '--upgrade', library, '--break-system-packages'],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                        )
                        console.print(
                            f"✅ Successfully updated [blue]{library}[/blue] to version {latest_version}.",
                            style="success"
                        )
                    except subprocess.CalledProcessError as e:
                        error_console.print(
                            f"❗ Failed to update [blue]{library}[/blue]: {e.stderr.decode()}"
                        )
                        console.print(
                            f"❗ If you want to use the latest version of [blue]{library}[/blue], " +
                            "Update it by running [bold red link=https://github.com/VOLT5775/VoLTGoLD-YT] " +
                            f"pip install --upgrade {library}[/bold red link]"
                        )

            else:
                error_console.print(
                    f"❗ Error checking for updates: {r.status_code}")
    except Exception as error:
        error_console.print(f"❗ Error checking for updates: {error}")


# main utils
def check_internet_connection() -> bool:
    """
    Checks if an internet connection is available.

    Returns:
        bool: True if internet connection is available, False otherwise.
    """
    if not is_internet_available():
        error_console.print("❗ No internet connection")
        return False

    console.print("✅ There is internet connection", style="success")
    console.print()
    return True


def asking_video_or_audio(download_service) -> None:
    """
    Handles video link scenario and downloads based on user choice.
    
    Args:
        download_service: The download service instance
    """
    file_type_choice = file_type().lower()
    is_audio = file_type_choice.startswith("audio")

    if file_type_choice.startswith(CANCEL_PREFIX.lower()):
        error_console.print("❗ Cancel the download...")
        sys.exit()
    
    elif is_audio:
        # تحميل الصوت
        download_service.is_audio = True
        video_obj, video_id, _, video_audio, _ = download_service.download_preparing()
        download_service.download_audio(video_obj, video_audio, video_id)
    
    else:
        # تحميل الفيديو - التصحيح هنا
        video_obj, video_id, streams, video_audio, quality = download_service.download_preparing()
        
        # streams بالفعل هو video_stream، لا حاجة لـ get_video_streams
        # فقط استخدم streams مباشرة
        download_service.download_video(video_obj, video_id, streams)
        
        
def asking_video_or_audio_for_playlist():
    """
    دالة خاصة لـ PlaylistHandler تسأل عن نوع التنزيل
    تُرجع True للصوت، False للفيديو، أو ترفع استثناء إذا تم الإلغاء
    """
    try:
        # الطريقة الصحيحة مع questionary
        
        
        file_type_choice = questionary.select(
            message="Choose the file type you want to download:",
            choices=["Video", "Audio", "Cancel"]
        ).ask()
        
        if file_type_choice is None or file_type_choice == "Cancel":
            raise TypeError("Cancelled by user")
        
        return file_type_choice.lower().startswith("audio")
        
    except KeyboardInterrupt:
        raise TypeError("Cancelled by user")
    except Exception as e:
        console.print(f"Selection error: {e}")
        raise TypeError("Cancelled")        