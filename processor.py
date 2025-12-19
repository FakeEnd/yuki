import os
import re
import time
from extractors import youtube, bilibili
from summarizer import summarize
from audio_handler import process_video_audio
import database
import notion_publisher

def sanitize_filename(name):
    return re.sub(r'[^\w\-_ \u4e00-\u9fa5]', '_', name).strip()

def process_video(url, platform=None, uploader_name="Unknown", title=None, video_id=None, distinct_folder=True):
    """
    Main processing logic.
    distinct_folder: If True, saves to output/[UploaderName]/...
    """
    if "youtube.com" in url or "youtu.be" in url:
        platform = "youtube"
        extractor = youtube
    elif "bilibili.com" in url:
        platform = "bilibili"
        extractor = bilibili
    else:
        print("Unsupported URL")
        return False

    # 1. Get Video ID (if not provided)
    if not video_id:
        if platform == "youtube":
            video_id = youtube.get_video_id(url)
        else:
            video_id = bilibili.get_bvid(url)

    # 2. Check Database (Notion & Local)
    # Priority: Notion (for cloud persistence)
    if notion_publisher.is_video_processed_notion(url):
         print(f"Video {url} already in Notion. Skipping.")
         return True
         
    if database.is_video_processed(video_id):
        print(f"Video {video_id} already in local DB. Skipping.")
        return True

    print(f"Processing {url} ({platform})...")

    # 3. Extract Transcript
    transcript = extractor.extract_transcript(url)
    
    # 4. Fallback to Audio
    audio_used = False
    if not transcript:
        print("Transcript not found in subtitles. Attempting audio fallback...")
        transcript = process_video_audio(url)
        audio_used = True
    
    if not transcript:
        print("Failed to get content from subtitles or audio.")
        return False

    # 5. Summarize
    print(f"Content extracted ({len(transcript)} chars). Summarizing...")
    try:
        summary_text = summarize(transcript)
    except Exception as e:
        print(f"Summarization failed: {e}")
        return False

    # 6. Save Output (Local File + Notion)
    
    # ... (Local file saving logic) ...
    
    date_str = time.strftime("%Y-%m-%d")
    
    # Create folder structure and save file
    safe_uploader = sanitize_filename(uploader_name)
    output_dir = f"output/{safe_uploader}"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if not title:
        title = f"Video_{video_id}"
    
    safe_title = sanitize_filename(title)
    safe_title = safe_title[:50]
    filename = f"{safe_title} - {date_str}.md"
    filepath = os.path.join(output_dir, filename)
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# Summary: {title}\n\n")
            f.write(f"**URL**: {url}\n")
            f.write(f"**Date**: {date_str}\n\n")
            f.write(summary_text)
        print(f"Summary saved to {filepath}")
        
        # 7. Record in Notion
        notion_publisher.publish_to_notion(
            title=title,
            url=url,
            platform=platform,
            summary_text=summary_text,
            publish_date_str=date_str
        )
        
        # 8. Record in Local DB
        database.add_processed_video(
            video_id=video_id,
            title=title,
            uploader_id=safe_uploader, 
            platform=platform,
            publish_date=int(time.time()), 
            summary_path=filepath,
            audio_downloaded=audio_used
        )
        return True

    except Exception as e:
        print(f"Error saving results: {e}")
        return False
