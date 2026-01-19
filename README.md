# Instagram to Apple Music Song Scraper

A Python script that automatically scrapes songs from an Instagram user's posts (especially Reels) and adds them to your Apple Music library.

## Features

- Scrapes songs from Instagram posts and Reels
- Automatically searches and adds songs to Apple Music
- Supports both authenticated and anonymous Instagram access
- Configurable number of posts to scrape
- Dry-run mode to preview without adding songs
- CSV export of results
- Comprehensive error handling and logging
- Rate limiting to respect API limits

## Prerequisites

- Python 3.7 or higher
- Instagram account (optional, for better access)
- Apple Developer account
- Apple Music subscription

## Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Create a virtual environment (recommended)**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

## Configuration

### Step 1: Apple Music API Setup

To add songs to Apple Music, you need to set up Apple Music API credentials. This is the most complex part but only needs to be done once.

#### 1.1 Create a MusicKit Identifier

1. Go to [Apple Developer Account](https://developer.apple.com/account/)
2. Log in with your Apple ID
3. Navigate to **Certificates, Identifiers & Profiles**
4. Click **Identifiers** in the sidebar
5. Click the **+** button to create a new identifier
6. Select **Media IDs** and click **Continue**
7. Enter a description (e.g., "Instagram to Apple Music")
8. Click **Continue** and then **Register**

#### 1.2 Create a MusicKit Private Key

1. In the same **Certificates, Identifiers & Profiles** section
2. Click **Keys** in the sidebar
3. Click the **+** button to create a new key
4. Enter a name (e.g., "MusicKit Key")
5. Check the box for **MusicKit**
6. Click **Continue** and then **Register**
7. **Download the key file** (AuthKey_XXXXXXXXXX.p8)
   - **IMPORTANT**: Save this file securely - you cannot download it again!
8. Note down the **Key ID** displayed on the page

#### 1.3 Get Your Team ID

1. Go to [Apple Developer Membership](https://developer.apple.com/account/#/membership/)
2. Your **Team ID** is displayed on this page
3. Copy and save it for the configuration

#### 1.4 Generate a User Token

This is required to modify your Apple Music library. You have two options:

**Option A: Use the Web-based Token Generator (Easiest)**

1. Visit [Apple's MusicKit JS Demo](https://developer.apple.com/documentation/applemusicapi/getting_keys_and_creating_tokens)
2. Follow the instructions to generate a user token
3. This token expires after 6 months

**Option B: Create Your Own Token Generator**

You'll need to create a simple web page that uses MusicKit JS to authenticate. Here's a minimal example:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Apple Music Token Generator</title>
    <script src="https://js-cdn.music.apple.com/musickit/v3/musickit.js"></script>
</head>
<body>
    <button id="auth">Authorize</button>
    <div id="token"></div>

    <script>
        document.addEventListener('musickitloaded', function() {
            MusicKit.configure({
                developerToken: 'YOUR_DEVELOPER_TOKEN_HERE',
                app: {
                    name: 'Instagram to Apple Music',
                    build: '1.0'
                }
            });

            const music = MusicKit.getInstance();

            document.getElementById('auth').addEventListener('click', async function() {
                await music.authorize();
                const userToken = music.musicUserToken;
                document.getElementById('token').innerText = 'User Token: ' + userToken;
            });
        });
    </script>
</body>
</html>
```

### Step 2: Instagram Configuration (Optional)

Instagram scraping can work without authentication, but authenticated access provides better reliability:

- Your Instagram username
- Your Instagram password

**Note**: Your credentials are only used locally and never sent anywhere except Instagram's official API.

### Step 3: Create .env File

1. Copy the example environment file:

   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and fill in your credentials:

   ```bash
   # Instagram Configuration (Optional)
   INSTAGRAM_USERNAME=your_instagram_username
   INSTAGRAM_PASSWORD=your_instagram_password

   # Apple Music API Configuration
   APPLE_TEAM_ID=A1B2C3D4E5
   APPLE_KEY_ID=X9Y8Z7W6V5
   APPLE_PRIVATE_KEY_PATH=/path/to/AuthKey_XXXXX.p8

   # Apple Music User Token
   APPLE_MUSIC_USER_TOKEN=your_long_user_token_here

   # Script Configuration
   TARGET_INSTAGRAM_USER=username_to_scrape
   MAX_POSTS=100
   DRY_RUN=false
   LOG_LEVEL=INFO
   ```

## Usage

### Basic Usage

Scrape songs from an Instagram user and add them to Apple Music:

```bash
python instagram_to_apple_music.py
```

This will use the configuration from your `.env` file.

### Command Line Options

```bash
# Scrape a specific user (overrides .env)
python instagram_to_apple_music.py --user some_instagram_user

# Scrape only the last 50 posts
python instagram_to_apple_music.py --posts 50

# Dry run - see what would be added without actually adding
python instagram_to_apple_music.py --dry-run

# Save results to a CSV file
python instagram_to_apple_music.py --output results.csv

# Set log level
python instagram_to_apple_music.py --log-level DEBUG

# Combine options
python instagram_to_apple_music.py --user some_user --posts 50 --dry-run --output results.csv
```

### Example Workflow

1. **First, do a dry run to see what would be added:**

   ```bash
   python instagram_to_apple_music.py --user your_favorite_artist --posts 20 --dry-run
   ```

2. **If everything looks good, run it for real:**

   ```bash
   python instagram_to_apple_music.py --user your_favorite_artist --posts 20 --output results.csv
   ```

3. **Check the logs for details:**

   ```bash
   cat logs/instagram_to_apple_music_*.log
   ```

## Project Structure

```
.
├── instagram_to_apple_music.py  # Main script
├── instagram_scraper.py          # Instagram scraping module
├── apple_music.py                # Apple Music API integration
├── requirements.txt              # Python dependencies
├── .env.example                  # Example environment variables
├── .gitignore                    # Git ignore file
├── README.md                     # This file
└── logs/                         # Log files (created at runtime)
```

## How It Works

1. **Instagram Scraping**: Uses `instaloader` to fetch posts from the target user
2. **Song Extraction**: Parses post metadata to extract song title and artist
3. **Apple Music Search**: Searches Apple Music catalog for each song
4. **Library Addition**: Adds found songs to your Apple Music library
5. **Reporting**: Generates a summary of added songs, failures, and not found songs

## Troubleshooting

### Instagram Issues

**Problem**: "Login failed" or "Two-factor authentication required"

**Solution**:
- Try running without authentication (remove Instagram credentials from .env)
- If using 2FA, you may need to generate an app-specific password
- Instagram may rate-limit anonymous access - try with fewer posts first

**Problem**: "No songs found"

**Solution**:
- The target user might not have many posts with music
- Try scraping a user known to post Reels with music
- Instagram's API doesn't always expose music metadata reliably

### Apple Music Issues

**Problem**: "Failed to generate developer token"

**Solution**:
- Ensure your .p8 key file path is correct
- Verify your Team ID and Key ID are correct
- Make sure the key file has the correct permissions (readable)

**Problem**: "Cannot add to library: No user token provided"

**Solution**:
- You must generate a user token using MusicKit JS
- The user token is different from the developer token
- User tokens expire after 6 months

**Problem**: "Song not found in Apple Music catalog"

**Solution**:
- The song might not be available in Apple Music
- The song title/artist extracted from Instagram might not match Apple Music's catalog
- Try searching for the song manually in Apple Music to verify it exists

### Rate Limiting

**Problem**: "Too many requests" errors

**Solution**:
- The script includes built-in delays between requests
- If you still hit rate limits, try reducing the number of posts
- Wait a few minutes and try again

## Limitations

- Instagram's API doesn't always expose music metadata reliably
- Song extraction depends on how Instagram structures post data
- Some songs on Instagram might not be available on Apple Music
- User tokens for Apple Music expire after 6 months
- Rate limiting on both Instagram and Apple Music

## Security Notes

- Never commit your `.env` file to version control
- Keep your Apple Music private key (.p8 file) secure
- Instagram credentials are only used locally
- All API credentials are stored locally and not transmitted except to official APIs

## Contributing

Improvements and bug fixes are welcome! Areas for potential enhancement:

- Better song metadata extraction from Instagram
- Support for Spotify/other music services
- Playlist creation instead of library addition
- Better matching algorithm for ambiguous song names
- GUI interface

## License

This project is for educational and personal use. Make sure to comply with Instagram's and Apple's terms of service.

## Disclaimer

This tool is not affiliated with, endorsed by, or officially connected with Instagram, Apple, or Apple Music. Use at your own risk and ensure you comply with all applicable terms of service.
