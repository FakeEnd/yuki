import os
from notion_client import Client
from dotenv import load_dotenv
import time

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

import requests

def is_video_processed_notion(url):
    """
    Checks if a video URL already exists in the Notion Database.
    We use the 'URL' property for this check.
    """
    if not NOTION_TOKEN or not DATABASE_ID:
        return False
        
    try:
        api_url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
        headers = {
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
        payload = {
            "filter": {
                "property": "URL",
                "url": {
                    "equals": url
                }
            }
        }
        
        response = requests.post(api_url, headers=headers, json=payload)
        
        if response.status_code != 200:
            print(f"Notion API Error: {response.text}")
            return False
            
        data = response.json()
        return len(data.get("results", [])) > 0

    except Exception as e:
        print(f"Error querying Notion: {e}")
        return False

def publish_to_notion(title, url, platform, summary_text, publish_date_str=None):
    """
    Creates a new page in the Notion Database.
    """
    if not NOTION_TOKEN or not DATABASE_ID:
        print("Notion credentials missing.")
        return False

    # Notion limits text blocks to 2000 chars. Need to chunk summary.
    # But usually inside a page we can just add paragraph blocks.
    
    # Chunking function
    def chunk_text(text, length=2000):
        return [text[i:i+length] for i in range(0, len(text), length)]

    children_blocks = []
    
    # Add summary as paragraphs
    for chunk in chunk_text(summary_text):
        children_blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": chunk
                        }
                    }
                ]
            }
        })

    try:
        if not publish_date_str:
            publish_date_str = time.strftime("%Y-%m-%d")

        new_page = {
            "Name": {"title": [{"text": {"content": title}}]},
            "URL": {"url": url},
            "Platform": {"select": {"name": platform}},
            "Date": {"date": {"start": publish_date_str}}
        }
        
        api_url = "https://api.notion.com/v1/pages"
        headers = {
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
        payload = {
            "parent": {"database_id": DATABASE_ID},
            "properties": new_page,
            "children": children_blocks
        }
        
        response = requests.post(api_url, headers=headers, json=payload)
        
        if response.status_code != 200:
            print(f"Notion Publish Error: {response.text}")
            print("Please ensure your Notion Database has 'Name' (title), 'URL' (url), 'Platform' (select), and 'Date' (date) columns.")
            return False
            
        print(f"Published to Notion: {title}")
        return True
    except Exception as e:
        print(f"Error publishing to Notion: {e}")
        return False
