import re
import json
import requests
# Using a simpler request-based approach for Bilibili to avoid complex async lib setup for now if possible,
# or we can use bilibili_api if this fails. Bilibili subtitles are often in protobuf or json.
# Let's try to find a library or use a known API endpoint.
# Actually, let's use bilibili_api library as planned, but wrap it in sync.

import asyncio
from bilibili_api import video, sync

def get_bvid(url):
    """
    Extract BVid from URL.
    """
    match = re.search(r'(BV\w+)', url)
    if match:
        return match.group(1)
    return None

def extract_transcript(url):
    """
    Extracts transcript/subtitles from a Bilibili video URL.
    Returns a single string of text.
    """
    bvid = get_bvid(url)
    if not bvid:
        raise ValueError(f"Could not extract BVid from {url}")

    async def _get_subtitle():
        v = video.Video(bvid=bvid)
        # Get video info to find cid (if needed) or just get subtitles
        # bilibili-api has get_subtitle
        try:
             # We might need to get the view info first to see available subtitles
            info = await v.get_info()
            # The library might have changed, but let's try getting subtitle URL
            # Note: explicit subtitle fetching might be needed.
            # Let's check available subtitles
            # This is complex without docs. Let's try a simpler approach if the library is too complex blindly.
            # But let's try the standard way.
            
            # Alternative: web scraping the initial state (often contains subtitle info)
            pass
        except Exception as e:
            print(f"Error interacting with Bilibili API: {e}")
            return None

    # Let's use a reliable scraping method or the library.
    # The library `bilibili_api` is good but sometimes requires credential.
    # Let's try `bilibili-api-python` standard usage.
    
    try:
        # Create video object
        v = video.Video(bvid=bvid)
        
        # Get info to find cid
        # We need headers for requests
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
            'Referer': f'https://www.bilibili.com/video/{bvid}/'
        }
        
        info = sync(v.get_info())
        cid = info['cid']
        
        params = {'bvid': bvid, 'cid': cid}
        # https://api.bilibili.com/x/player/v2 might need login or wbi signature
        # Try a simpler public endpoint or scrape from get_info response if subtitles are there?
        # get_info (v2) response usually doesn't have subtitles.
        # But let's try calling the player api with headers.
        
        resp = requests.get('https://api.bilibili.com/x/player/v2', params=params, headers=headers)
        
        try:
            data = resp.json()
        except json.JSONDecodeError:
            print(f"Failed to decode JSON from Bilibili API. Response: {resp.text[:100]}...")
            return None
        
        subtitle_url = None
        if data['code'] == 0 and 'subtitle' in data['data']:
            subs = data['data']['subtitle']['subtitles']
            if subs:
                subtitle_url = subs[0]['url']
                if subtitle_url.startswith('//'):
                    subtitle_url = 'https:' + subtitle_url
        
        if subtitle_url:
            sub_resp = requests.get(subtitle_url, headers=headers)
            try:
                sub_data = sub_resp.json()
                # body contains list of {from, to, content}
                full_text = " ".join([item['content'] for item in sub_data['body']])
                return full_text
            except json.JSONDecodeError:
                print("Failed to decode subtitle JSON.")
                return None
            
        return None

    except Exception as e:
        print(f"Error extracting Bilibili transcript: {e}")
        return None
