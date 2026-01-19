"""
Instagram Scraper Module

This module handles scraping Instagram posts and extracting song information
from posts (especially Reels) that contain music.
"""

import instaloader
import logging
import time
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Song:
    """Data class to represent a song extracted from Instagram"""
    title: str
    artist: str
    post_url: Optional[str] = None

    def __hash__(self):
        return hash((self.title.lower(), self.artist.lower()))

    def __eq__(self, other):
        if not isinstance(other, Song):
            return False
        return (self.title.lower() == other.title.lower() and
                self.artist.lower() == other.artist.lower())

    def __str__(self):
        return f"{self.title} by {self.artist}"


class InstagramScraper:
    """
    Scraper for extracting song information from Instagram posts.

    This class uses instaloader to fetch posts from a specific Instagram user
    and extracts music information from those posts.
    """

    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize the Instagram scraper.

        Args:
            username: Instagram username for authentication (optional)
            password: Instagram password for authentication (optional)
        """
        self.loader = instaloader.Instaloader(
            download_pictures=False,
            download_videos=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
            post_metadata_txt_pattern='',
        )

        self.authenticated = False
        if username and password:
            try:
                self.loader.login(username, password)
                self.authenticated = True
                logger.info("Successfully authenticated with Instagram")
            except Exception as e:
                logger.warning(f"Failed to authenticate with Instagram: {e}")
                logger.info("Proceeding with anonymous access (limited functionality)")

    def scrape_songs(self, target_username: str, max_posts: int = 100) -> List[Song]:
        """
        Scrape songs from a target Instagram user's posts.

        Args:
            target_username: Instagram username to scrape
            max_posts: Maximum number of posts to scrape (default 100)

        Returns:
            List of unique Song objects found in the posts
        """
        logger.info(f"Starting to scrape songs from @{target_username}")

        try:
            profile = instaloader.Profile.from_username(
                self.loader.context,
                target_username
            )
        except Exception as e:
            logger.error(f"Failed to fetch profile for @{target_username}: {e}")
            return []

        songs = set()
        posts_checked = 0

        try:
            for post in profile.get_posts():
                if posts_checked >= max_posts:
                    break

                posts_checked += 1

                # Extract song information from post
                song = self._extract_song_from_post(post)
                if song:
                    songs.add(song)
                    logger.info(f"Found song: {song}")

                # Be polite with rate limiting
                time.sleep(1)

                if posts_checked % 10 == 0:
                    logger.info(f"Processed {posts_checked} posts, found {len(songs)} unique songs so far")

        except instaloader.exceptions.ConnectionException as e:
            logger.error(f"Connection error while scraping: {e}")
        except Exception as e:
            logger.error(f"Unexpected error while scraping: {e}")

        logger.info(f"Scraping complete: Checked {posts_checked} posts, found {len(songs)} unique songs")
        return list(songs)

    def _extract_song_from_post(self, post) -> Optional[Song]:
        """
        Extract song information from a single Instagram post.

        Args:
            post: instaloader Post object

        Returns:
            Song object if music found, None otherwise
        """
        try:
            # Check if post has title (common for Reels with music)
            if hasattr(post, 'title') and post.title:
                # Try to parse title for song information
                # Instagram often formats as "Song Title · Artist Name"
                if '·' in post.title:
                    parts = post.title.split('·')
                    if len(parts) >= 2:
                        title = parts[0].strip()
                        artist = parts[1].strip()
                        return Song(
                            title=title,
                            artist=artist,
                            post_url=f"https://www.instagram.com/p/{post.shortcode}/"
                        )

            # Check for accessibility caption which sometimes contains music info
            if hasattr(post, 'accessibility_caption') and post.accessibility_caption:
                caption = post.accessibility_caption.lower()
                if 'music' in caption or 'audio' in caption:
                    # Extract from caption if possible
                    # This is less reliable but can work
                    pass

            # Check if post is a video (Reels) which are more likely to have music
            if hasattr(post, 'is_video') and post.is_video:
                # Try to get media product type
                if hasattr(post, 'media_product_type'):
                    if post.media_product_type == 'clips':  # This is a Reel
                        # Instaloader doesn't directly expose music metadata
                        # but we can try to get it from the caption or comments
                        caption = post.caption if post.caption else ""

                        # Look for common music-related hashtags or mentions
                        # Format: Song Name - Artist Name
                        if '-' in caption and ('♫' in caption or '🎵' in caption or '🎶' in caption):
                            # Try to extract song info from caption
                            lines = caption.split('\n')
                            for line in lines:
                                if '♫' in line or '🎵' in line or '🎶' in line:
                                    # Remove emoji and try to parse
                                    line = line.replace('♫', '').replace('🎵', '').replace('🎶', '').strip()
                                    if '-' in line:
                                        parts = line.split('-')
                                        if len(parts) >= 2:
                                            title = parts[0].strip()
                                            artist = parts[1].strip()
                                            return Song(
                                                title=title,
                                                artist=artist,
                                                post_url=f"https://www.instagram.com/p/{post.shortcode}/"
                                            )

        except Exception as e:
            logger.debug(f"Error extracting song from post: {e}")

        return None


def test_scraper():
    """Test function for the Instagram scraper"""
    import os
    from dotenv import load_dotenv

    load_dotenv()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    username = os.getenv('INSTAGRAM_USERNAME')
    password = os.getenv('INSTAGRAM_PASSWORD')
    target_user = os.getenv('TARGET_INSTAGRAM_USER', 'instagram')

    scraper = InstagramScraper(username, password)
    songs = scraper.scrape_songs(target_user, max_posts=10)

    print(f"\nFound {len(songs)} songs:")
    for song in songs:
        print(f"  - {song}")


if __name__ == '__main__':
    test_scraper()
