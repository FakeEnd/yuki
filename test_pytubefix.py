from pytubefix import YouTube
from pytubefix.cli import on_progress
import os

url = "https://www.youtube.com/watch?v=fT_ebTsIJHs"

def download_audio_pytubefix():
    print(f"Attempting download with pytubefix for {url}")
    try:
        yt = YouTube(url, on_progress_callback=on_progress)
        print(f"Title: {yt.title}")
        
        # Get audio only stream
        ys = yt.streams.get_audio_only()
        if not ys:
            print("No audio stream found.")
            return

        print("Downloading...")
        # Download to current directory
        out_file = ys.download(filename="pytubefix_audio")
        
        # Renaissance of extensions
        import os
        base, ext = os.path.splitext(out_file)
        new_file = base + '.m4a'
        if os.path.exists(new_file):
            os.remove(new_file)
        os.rename(out_file, new_file)
        
        print(f"Downloaded to {new_file}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    download_audio_pytubefix()
