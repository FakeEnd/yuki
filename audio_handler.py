import os
import yt_dlp
from openai import OpenAI
import time

def download_audio(url, output_filename="temp_audio"):
    """
    Downloads audio from the given URL using yt-dlp.
    Returns the path to the downloaded audio file.
    """
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f"{output_filename}.%(ext)s",
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'referer': 'https://www.youtube.com/',
    }
    
    if os.path.exists('cookies.txt'):
        ydl_opts['cookiefile'] = 'cookies.txt'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            ext = info.get('ext', 'm4a')
            downloaded_path = f"{output_filename}.{ext}"
            
            if os.path.exists(downloaded_path):
                return downloaded_path
            
            # fallback: look for any file starting with output_filename
            for file in os.listdir('.'):
                if file.startswith(output_filename):
                    return file
                    
            
            return None
    except Exception as e:
        print(f"Error downloading with yt-dlp: {e}")
        print("Attempting fallback with pytubefix...")
        return download_audio_pytubefix(url, output_filename)

def download_audio_pytubefix(url, output_filename):
    """
    Fallback downloader using pytubefix.
    """
    from pytubefix import YouTube
    from pytubefix.cli import on_progress
    
    try:
        yt = YouTube(url, on_progress_callback=on_progress)
        ys = yt.streams.get_audio_only()
        if not ys:
            return None
            
        print("Downloading with pytubefix...")
        out_file = ys.download(filename=output_filename)
        
        # Rename to m4a for consistency if needed, though pytubefix usually does it right or gives m4a/mp4
        # Check what we got
        import os
        base, ext = os.path.splitext(out_file)
        new_file = f"{output_filename}.m4a"
        
        # If it's already right, good. If not, rename.
        if out_file != new_file:
            if os.path.exists(new_file):
                os.remove(new_file)
            os.rename(out_file, new_file)
            
        return new_file
    except Exception as e:
        print(f"Error downloading with pytubefix: {e}")
        return None

def transcribe_audio(file_path):
    """
    Transcribes the audio file using OpenAI Whisper.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found.")

    client = OpenAI(api_key=api_key)

    try:
        with open(file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )
        return transcript.text
    except Exception as e:
        print(f"Error during transcription: {e}")
        return None
    finally:
        # Cleanup
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass

def process_video_audio(url):
    """
    Orchestrates downloading and transcribing.
    """
    print("Fallback: Attempting to download and transcribe audio...")
    
    # Create cache dir
    if not os.path.exists("audio_cache"):
        os.makedirs("audio_cache")
        
    # Use a unique filename to avoid collisions/locks
    # Save to audio_cache/
    filename = f"audio_cache/audio_{int(time.time())}"
    
    audio_path = download_audio(url, filename)
    if not audio_path:
        print("Audio download failed.")
        return None
    
    print(f"Audio downloaded to {audio_path}. Transcribing...")
    text = transcribe_audio(audio_path)
    return text
