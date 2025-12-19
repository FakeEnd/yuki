import asyncio
import time
import os
from bilibili_api import user, sync
from dotenv import load_dotenv
import processor
import database

# Load env vars
load_dotenv()

# Target Uploader ID (Space ID) for Bilibili
BILIBILI_UID = 1515375273 
# Target Channel URL for YouTube
# Using /videos to ensure we get chronological uploads
YOUTUBE_CHANNEL = "https://www.youtube.com/@SavvyCapitalist%E8%81%AA%E6%98%8E%E5%B0%8F%E8%B5%84/videos"

# Configure Bilibili User Agent to avoid 412
import bilibili_api
# settings.user_agent is not available in all versions, but HEADERS is a global dict
bilibili_api.HEADERS["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


# Helper to load cookies for Cloud Execution
def load_cookies():
    cookie_content = os.getenv("COOKIES_TXT")
    if cookie_content:
        # Create cookies.txt from secret
        with open("cookies.txt", "w") as f:
            f.write(cookie_content)
        print("Generated cookies.txt from environment variable.")

# Load env vars
load_cookies()


async def check_new_videos(uid):
    # ... (Keep existing Bilibili logic, renamed slightly for clarity or just kept as is)
    print(f"Checking Bilibili videos for user {uid}...")
    try:
        # Check for credentials in env
        sessdata = os.getenv("BILIBILI_SESSDATA")
        bili_jct = os.getenv("BILIBILI_JCT")
        buvid3 = os.getenv("BILIBILI_BUVID3")
        
        credential = None
        if sessdata and bili_jct and buvid3:
            from bilibili_api import Credential
            print("Using Bilibili Credentials from environment.")
            credential = Credential(sessdata=sessdata, bili_jct=bili_jct, buvid3=buvid3)
            
        u = user.User(uid, credential=credential)
        user_info = await u.get_user_info()
        uploader_name = user_info['name']
        print(f"Bilibili Uploader: {uploader_name}")

        videos_data = await u.get_videos(ps=10) 
        videos = videos_data['list']['vlist']
        
        current_time = time.time()
        processed_count = 0
        
        for v in videos:
            bvid = v['bvid']
            title = v['title']
            created = v['created']
            age = current_time - created
            
            if age <= 86400: # 24 hours
                print(f"Found new Bilibili video: {title} ({bvid}) - {age/3600:.1f}h ago")
                url = f"https://www.bilibili.com/video/{bvid}"
                success = processor.process_video(
                    url=url, 
                    platform="bilibili",
                    uploader_name=uploader_name,
                    title=title,
                    video_id=bvid
                )
                if success:
                    processed_count += 1
        
        if processed_count > 0:
            print(f"Processed {processed_count} new Bilibili videos.")
        else:
            print("No new Bilibili videos found.")

    except Exception as e:
        print(f"Error checking Bilibili: {e}")

def check_youtube_new_videos(channel_url):
    print(f"Checking YouTube videos for {channel_url}...")
    import yt_dlp
    import datetime
    import os

    # Configure yt-dlp to just get metadata (fast)
    # --flat-playlist: don't download, just list
    # --playlist-end 10: check last 10 videos
    ydl_opts = {
        'extract_flat': True,
        'playlistend': 10,
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    # Try using cookies if available (helps with 403 on channel pages too sometimes)
    if os.path.exists('cookies.txt'):
         ydl_opts['cookiefile'] = 'cookies.txt'

    try:
        processed_count = 0
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(channel_url, download=False)
            
            uploader_name = info.get('uploader', 'Unknown_YouTuber')
            # Fallback if top level uploader is generic, sometimes it's in entries
            if uploader_name == 'Unknown_YouTuber' and info.get('entries'):
                uploader_name = info['entries'][0].get('uploader', 'YouTube_Channel')
                
            print(f"YouTube Uploader: {uploader_name}")
            
            entries = info.get('entries', [])
            current_time = time.time()
            
            for entry in entries:
                video_id = entry.get('id')
                title = entry.get('title')
                url = entry.get('url') # or construct https://www.youtube.com/watch?v={id}
                if not url:
                    url = f"https://www.youtube.com/watch?v={video_id}"

                # yt-dlp flat extraction might not give exact timestamp, usually gives upload_date like '20231218'
                # or 'timestamp' if available. entries usually have 'timestamp' set to None for flat extraction sometimes.
                # But 'upload_date' is reliable 'YYYYMMDD'.
                # For 24h check, strict timestamp is better.
                # If we only have date, we assume 00:00 of that date, which might be risky.
                # However, for flat playlist, often we don't get full details. 
                # Improving: We can check if video_id is in DB first. If so, skip.
                # If not in DB, we fetch full info OR just rely on upload_date matching today/yesterday.
                
                
                # Check DB first to save time
                if database.is_video_processed(video_id):
                    continue
                
                # If flat extraction didn't give date, we must fetch full info for this video
                upload_date_str = entry.get('upload_date')
                
                if not upload_date_str:
                    print(f"Fetching full details for candidate: {title}")
                    try:
                        # Create a new YDL instance or reuse? Reusing is fine but we need different opts if we want full info?
                        # actually existing opts are 'extract_flat': True. We need a new instance/opts for full extraction logic
                        # or just overriding.
                         opts_full = {'quiet':True, 'no_warnings':True}
                         if os.path.exists('cookies.txt'):
                             opts_full['cookiefile'] = 'cookies.txt'
                         
                         with yt_dlp.YoutubeDL(opts_full) as ydl_full:
                             full_info = ydl_full.extract_info(url, download=False)
                             upload_date_str = full_info.get('upload_date')
                    except Exception as e:
                        print(f"Could not fetch full info for {url}: {e}")
                        continue

                if not upload_date_str:
                    print(f"Still no date for {title}, skipping.")
                    continue
                    
                # Convert to date object
                upload_date = datetime.datetime.strptime(upload_date_str, "%Y%m%d").date()
                today = datetime.datetime.now().date()
                yesterday = today - datetime.timedelta(days=1)
                
                # Simple check: is it today or yesterday?
                print(f"Checking {title} - Date: {upload_date} vs Threshold: {yesterday}")
                if upload_date >= yesterday:
                    print(f"Found new YouTube video candidate: {title} ({upload_date})")
                    # Process
                    success = processor.process_video(
                        url=url, 
                        platform="youtube",
                        uploader_name=uploader_name,
                        title=title,
                        video_id=video_id
                    )
                    if success:
                        processed_count += 1
                        
        if processed_count > 0:
            print(f"Processed {processed_count} new YouTube videos.")
        else:
            print("No new YouTube videos found.")

    except Exception as e:
        print(f"Error checking YouTube: {e}")

async def main_monitor():
    await check_new_videos(BILIBILI_UID)
    # YouTube check is blocking (sync), so just call it
    print("-" * 20)
    check_youtube_new_videos(YOUTUBE_CHANNEL)

if __name__ == "__main__":
    # Run the async loop
    asyncio.run(main_monitor())

