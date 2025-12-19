from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs

def get_video_id(url):
    """
    Extracts the video ID from a YouTube URL.
    """
    parsed_url = urlparse(url)
    if parsed_url.hostname == 'youtu.be':
        return parsed_url.path[1:]
    if parsed_url.hostname in ('www.youtube.com', 'youtube.com'):
        if parsed_url.path == '/watch':
            p = parse_qs(parsed_url.query)
            return p['v'][0]
        if parsed_url.path[:7] == '/embed/':
            return parsed_url.path.split('/')[2]
        if parsed_url.path[:3] == '/v/':
            return parsed_url.path.split('/')[2]
    # fail?
    return None

def extract_transcript(url):
    """
    Extracts transcript from a YouTube video URL.
    Returns a single string of text.
    """
    video_id = get_video_id(url)
    if not video_id:
        raise ValueError(f"Could not extract video ID from {url}")

    try:
        # Instantiate the API
        yt = YouTubeTranscriptApi()
        
        # Get transcript list
        transcript_list = yt.list(video_id)
        
        transcript = None
        
        # Try finding english first
        try:
            transcript = transcript_list.find_transcript(['en'])
        except:
            pass
            
        # Try finding generated english
        if not transcript:
            try:
                transcript = transcript_list.find_generated_transcript(['en'])
            except:
                pass
        
        # If still none, take the first available
        if not transcript:
            for t in transcript_list:
                transcript = t
                break
                
        if not transcript:
            return None

        # Fetch the content
        data = transcript.fetch()
        # Combine text
        full_text = " ".join([t.text for t in data])
        return full_text
        
    except Exception as e:
        print(f"Error getting transcript: {e}")
        return None
