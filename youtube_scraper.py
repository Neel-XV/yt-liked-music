import os
import csv
import logging
from tqdm import tqdm
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle

# Configuration
SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'
CLIENT_SECRETS_FILE = 'client_secrets.json'
TOKEN_PICKLE_FILE = 'token.pickle'
OUTPUT_FILE = 'liked_music.csv'

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import json

def get_authenticated_service():
    """Authenticates the user and returns the YouTube service object."""
    credentials = None
    
    if os.path.exists(TOKEN_PICKLE_FILE):
        with open(TOKEN_PICKLE_FILE, 'rb') as token:
            credentials = pickle.load(token)
            
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            if not os.path.exists(CLIENT_SECRETS_FILE):
                print(f"\nError: '{CLIENT_SECRETS_FILE}' not found.")
                print("Please download it from Google Cloud Console.")
                exit(1)
            
            # Check for credential type
            with open(CLIENT_SECRETS_FILE, 'r') as f:
                secrets_data = json.load(f)
                
            if 'web' in secrets_data:
                print("\n" + "!" * 60)
                print("CRITICAL: You are using a 'Web Application' credential.")
                print("Local scripts require a 'Desktop App' credential to work correctly.")
                print("\nHOW TO FIX:")
                print("1. Go to: https://console.cloud.google.com/apis/credentials")
                print("2. Click 'Create Credentials' -> 'OAuth client ID'.")
                print("3. Choose 'Desktop app' as the Application Type.")
                print("4. Download the new JSON, rename it to 'client_secrets.json',")
                print("   and replace the existing one in this folder.")
                print("!" * 60 + "\n")
                
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            # Use a fixed port to make it more predictable
            credentials = flow.run_local_server(port=8080)
            
        with open(TOKEN_PICKLE_FILE, 'wb') as token:
            pickle.dump(credentials, token)
            
    return build(API_SERVICE_NAME, API_VERSION, credentials=credentials)

def is_music_content(item):
    """
    Checks if a video item is likely music-related based on:
    - Category ID (10 = Music)
    - Channel title keywords
    - Title/Description keywords
    """
    snippet = item.get('snippet', {})
    content_details = item.get('contentDetails', {})
    
    # 1. Check Category ID
    category_id = snippet.get('categoryId')
    if category_id == '10':
        return True
        
    # 2. Check Channel Title
    channel_title = snippet.get('channelTitle', '').lower()
    music_channel_keywords = ['vevo', 'official artist channel', 'records', 'music', 'production', 'audio', 'label', 'records', 'entertainment']
    if any(keyword in channel_title for keyword in music_channel_keywords):
        return True
        
    # 3. Check Video Title/Description keywords
    title = snippet.get('title', '').lower()
    description = snippet.get('description', '').lower()
    music_keywords = ['official music video', 'official audio', 'lyrics video', 'ft.', 'feat.', 'remix', 'prod.', 'music by', 'directed by']
    
    if any(keyword in title for keyword in music_keywords):
        return True
        
    return False

def parse_song_info(item):
    """
    Attempts to parse song title and artist from the video title.
    Fallback to channel name if parsing fails.
    """
    snippet = item.get('snippet', {})
    video_title = snippet.get('title', '')
    channel_title = snippet.get('channelTitle', '')
    
    # Common separators
    separators = [' - ', ' – ', ' | ', ' : ', ': ']
    
    song_name = video_title
    artist_name = channel_title
    
    for sep in separators:
        if sep in video_title:
            parts = video_title.split(sep, 1)
            # Usually Artist - Song or Song - Artist
            # This is a heuristic, let's assume Artist - Song for now as it's common
            artist_name = parts[0].strip()
            song_name = parts[1].strip()
            break
            
    # Clean up song name from common suffixes
    suffixes = ['(Official Video)', '(Official Audio)', '[Official Video]', '[Official Audio]', '(Lyric Video)', '(HD)', '(4K)', '(Live)']
    for suffix in suffixes:
        song_name = song_name.replace(suffix, '').replace(suffix.lower(), '').strip()
        
    return {
        'Song Name': song_name,
        'Artist': artist_name,
        'URL': f"https://www.youtube.com/watch?v={item['id']}" if 'id' in item else f"https://www.youtube.com/watch?v={item['contentDetails']['videoId']}"
    }

def get_all_liked_videos(youtube):
    """Fetches all liked videos from the 'LL' (Liked Videos) playlist."""
    liked_videos = []
    next_page_token = None
    
    # First, get the total count if possible (playlistItems for 'LL' doesn't always show accurately, but we can try)
    # Actually, liked videos can be retrieved via list(myRating='like')
    
    print("Fetching liked videos...")
    
    try:
        while True:
            request = youtube.videos().list(
                part="snippet,contentDetails",
                myRating="like",
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()
            
            items = response.get('items', [])
            liked_videos.extend(items)
            
            next_page_token = response.get('nextPageToken')
            
            if not next_page_token:
                break
                
            print(f"Retrieved {len(liked_videos)} videos...", end='\r')
            
    except Exception as e:
        logger.error(f"Error fetching liked videos: {e}")
        
    print(f"\nFinished fetching. Total liked videos found: {len(liked_videos)}")
    return liked_videos

import argparse

def run_tests():
    """Runs a dry-run test with mock data to verify filtering and parsing logic."""
    print("Running in TEST mode with mock data...")
    mock_items = [
        {
            'id': 'video1',
            'snippet': {
                'title': 'Artist - Song Name (Official Video)',
                'channelTitle': 'ArtistVEVO',
                'categoryId': '10',
                'description': 'Check out this new music video.'
            }
        },
        {
            'id': 'video2',
            'snippet': {
                'title': 'Funny Cat Compilation 2024',
                'channelTitle': 'CatLovers',
                'categoryId': '15',
                'description': 'Meow.'
            }
        },
        {
            'id': 'video3',
            'snippet': {
                'title': 'New Song feat. Someone',
                'channelTitle': 'MusicLabel',
                'categoryId': '24', # Not Category 10
                'description': 'Official Audio'
            }
        }
    ]
    
    music_videos = []
    for item in mock_items:
        if is_music_content(item):
            parsed = parse_song_info(item)
            music_videos.append(parsed)
            
    print(f"Mock processed {len(mock_items)} videos.")
    print(f"Identified {len(music_videos)} as music.")
    for mv in music_videos:
        print(f" - {mv['Artist']} | {mv['Song Name']} ({mv['URL']})")

def main():
    parser = argparse.ArgumentParser(description="YouTube Liked Songs Scraper")
    parser.add_argument("--test", action="store_true", help="Run with mock data to verify logic")
    args = parser.parse_args()

    if args.test:
        run_tests()
        return

    try:
        youtube = get_authenticated_service()
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        return

    all_videos = get_all_liked_videos(youtube)
    
    music_videos = []
    print("Filtering and parsing music content...")
    
    for item in tqdm(all_videos, desc="Processing"):
        if is_music_content(item):
            parsed = parse_song_info(item)
            music_videos.append(parsed)
            
    # Remove duplicates based on URL
    seen_urls = set()
    unique_music = []
    for mv in music_videos:
        if mv['URL'] not in seen_urls:
            unique_music.append(mv)
            seen_urls.add(mv['URL'])
            
    # Save to CSV
    if unique_music:
        keys = unique_music[0].keys()
        with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(unique_music)
            
        print(f"\nSuccess! Found {len(unique_music)} music videos out of {len(all_videos)} liked videos.")
        print(f"Results saved to {OUTPUT_FILE}")
    else:
        print("\nNo music content identified.")

if __name__ == "__main__":
    main()
