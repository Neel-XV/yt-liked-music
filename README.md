# YouTube Liked Music Scraper 🎵

A Python tool to extract, filter, and export your liked songs from YouTube into a clean CSV format.

## Features
- **OAuth 2.0 Authentication**: Securely access your private "Liked Videos" using the official YouTube Data API.
- **Auto-Filtering**: Automatically separates music content from other liked videos (vlogs, tutorials, etc.) using category analysis and metadata parsing.
- **Smart Metadata Extraction**: Attempts to split video titles into *Artist* and *Song Name* fields.
- **CSV Export**: Generates a `liked_music.csv` file for easy import into other tools or spreadsheets.

## Setup Requirements

### 1. API Credentials
This script requires a `client_secrets.json` file from the [Google Cloud Console](https://console.cloud.google.com/):
1. Create a project and enable the **YouTube Data API v3**.
2. Configure the **OAuth Consent Screen** (set User Type to "External" and add your own email as a "Test User").
3. Create **OAuth 2.0 Client IDs** (Application Type: **Desktop App**).
4. Download the JSON, rename it to `client_secrets.json`, and place it in this directory.

### 2. Installation
```powershell
pip install -r requirements.txt
```

## Usage
Run the script:
```powershell
python youtube_scraper.py
```

To verify the filtering logic with mock data:
```powershell
python youtube_scraper.py --test
```

## Output
The script generates a `liked_music.csv` with the following columns:
- **Song Name**
- **Artist**
- **URL**

## Note
Your personal credentials (`client_secrets.json`) and tokens (`token.pickle`) are ignored by Git for security.
