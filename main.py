import argparse
import os
from dotenv import load_dotenv

def main():
    parser = argparse.ArgumentParser(description="Video Summarizer")
    parser.add_argument("url", help="URL of the video to summarize")
    args = parser.parse_args()

    load_dotenv()
    
    print(f"Processing URL: {args.url}")
    
    transcript = None
    try:
        if 'youtube.com' in args.url or 'youtu.be' in args.url:
            from extractors.youtube import extract_transcript
            transcript = extract_transcript(args.url)
        elif 'bilibili.com' in args.url:
            from extractors.bilibili import extract_transcript
            transcript = extract_transcript(args.url)
        else:
            print("Unsupported URL. Please use a YouTube or Bilibili video URL.")
            return

        if not transcript:
            print("Failed to extract transcript/subtitles directly. Attempting audio transcription fallback...")
            from audio_handler import process_video_audio
            transcript = process_video_audio(args.url)

        if not transcript:
            print("Failed to extract transcript from both subtitles and audio.")
            return

        print(f"Transcript extracted (Length: {len(transcript)} chars). Summarizing...")
        
        from summarizer import summarize
        summary = summarize(transcript)
        
        print("\n--- Summary ---\n")
        print(summary)
        print("\n----------------\n")
        
        # Save to output folder
        import time
        import re
        
        # simple sanitizer
        sanitized_url = re.sub(r'[^\w\-_]', '_', args.url)
        # Limit length
        sanitized_url = sanitized_url[-30:] 
        
        filename = f"output/summary_{int(time.time())}_{sanitized_url}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# Summary for {args.url}\n\n")
            f.write(summary)
            
        print(f"Summary saved to {filename}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
