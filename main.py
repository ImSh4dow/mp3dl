import os
import subprocess
import yt_dlp
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
from youtube_search import YoutubeSearch
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3

# Spotify API credentials
SPOTIPY_CLIENT_ID = "your_spotify_client_id"
SPOTIPY_CLIENT_SECRET = "your_spotify_client_secret"

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "MP3s")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# SoundCloud Downloader Path (inside virtual env)
SCDL_PATH = os.path.join(SCRIPT_DIR, ".venv/bin/scdl")

# Initialize Spotify API
sp = Spotify(auth_manager=SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET))

def sanitize_filename(filename):
    """Removes invalid characters for cross-platform compatibility."""
    return "".join(c if c.isalnum() or c in " -_" else "_" for c in filename)

def download_youtube_audio(url, filename=None):
    """Downloads YouTube audio and converts it to MP3 (128kbps)."""
    try:
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(OUTPUT_DIR, "%(title)s.%(ext)s"),
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "320",
                }
            ],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            video_title = info_dict.get("title", "Unknown")
            downloaded_file = os.path.join(OUTPUT_DIR, sanitize_filename(video_title) + ".mp3")

            print(f"✅ Downloaded and converted: {downloaded_file}")
            return downloaded_file

    except Exception as e:
        print(f"❌ Error downloading YouTube audio: {e}")
        return None

def download_spotify_track(url):
    """Finds a Spotify track on YouTube and downloads it as 128 kbps MP3."""
    try:
        track_id = url.split("/")[-1].split("?")[0]
        track_info = sp.track(track_id)
        track_name = track_info["name"]
        artist_name = track_info["artists"][0]["name"]
        search_query = f"{track_name} {artist_name}"

        results = YoutubeSearch(search_query, max_results=1).to_dict()
        if not results:
            print("❌ No YouTube video found for the track.")
            return None

        youtube_url = f"https://www.youtube.com{results[0]['url_suffix']}"
        mp3_file = download_youtube_audio(youtube_url)

        if mp3_file:
            tag_mp3(mp3_file, track_name, artist_name)
        return mp3_file
    except Exception as e:
        print(f"❌ Error downloading Spotify track: {e}")
        return None

def download_soundcloud_track(url):
    """Downloads a SoundCloud track using scdl."""
    try:
        command = [SCDL_PATH, "-l", url, "--path", OUTPUT_DIR]
        subprocess.run(command, check=True)
        print(f"✅ Downloaded SoundCloud track to {OUTPUT_DIR}")
    except FileNotFoundError:
        print("❌ Error: 'scdl' is not installed or not in PATH.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error downloading SoundCloud track: {e}")

def tag_mp3(file_path, title, artist):
    """Adds ID3 metadata to the MP3 file for DODOSOUL M800 compatibility."""
    try:
        audio = MP3(file_path, ID3=EasyID3)
        audio["title"] = title
        audio["artist"] = artist
        audio.save()
        print(f"✅ Tagged {file_path} with Title: {title}, Artist: {artist}")
    except Exception as e:
        print(f"❌ Error tagging MP3: {e}")

def recognize_service(url):
    """Recognizes whether a URL is from YouTube, Spotify, or SoundCloud."""
    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    elif "spotify.com" in url:
        return "spotify"
    elif "soundcloud.com" in url:
        return "soundcloud"
    return None

def search_and_download(query):
    """Searches for a track on YouTube and downloads it."""
    try:
        results = YoutubeSearch(query, max_results=1).to_dict()
        if not results:
            print("❌ No results found for the query.")
            return None

        youtube_url = f"https://www.youtube.com{results[0]['url_suffix']}"
        return download_youtube_audio(youtube_url)
    except Exception as e:
        print(f"❌ Error searching and downloading: {e}")
        return None

def main():
    user_input = input("🎵 Enter a URL or search query: ").strip()

    service = recognize_service(user_input)
    if service:
        if service == "youtube":
            download_youtube_audio(user_input)
        elif service == "spotify":
            download_spotify_track(user_input)
        elif service == "soundcloud":
            download_soundcloud_track(user_input)
        else:
            print("❌ Unsupported service.")
    else:
        search_and_download(user_input)

if __name__ == "__main__":
    main()
