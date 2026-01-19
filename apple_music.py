"""
Apple Music Integration Module

This module handles authentication with Apple Music API and adding songs
to the user's library.
"""

import requests
import logging
import time
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from pathlib import Path

logger = logging.getLogger(__name__)


class AppleMusicClient:
    """
    Client for interacting with Apple Music API.

    This class handles authentication and provides methods to search for songs
    and add them to the user's library.
    """

    BASE_URL = "https://api.music.apple.com/v1"

    def __init__(
        self,
        team_id: Optional[str] = None,
        key_id: Optional[str] = None,
        private_key_path: Optional[str] = None,
        developer_token: Optional[str] = None,
        user_token: Optional[str] = None
    ):
        """
        Initialize the Apple Music client.

        Args:
            team_id: Apple Developer Team ID
            key_id: MusicKit Key ID
            private_key_path: Path to the .p8 private key file
            developer_token: Pre-generated developer token (alternative to generating)
            user_token: User-specific music token (required for library modifications)
        """
        self.user_token = user_token

        # Generate or use provided developer token
        if developer_token:
            self.developer_token = developer_token
        elif team_id and key_id and private_key_path:
            self.developer_token = self._generate_developer_token(
                team_id, key_id, private_key_path
            )
        else:
            raise ValueError(
                "Must provide either developer_token or (team_id, key_id, private_key_path)"
            )

        if not self.user_token:
            logger.warning(
                "No user token provided. Library modification features will not work."
            )

        logger.info("Apple Music client initialized successfully")

    def _generate_developer_token(
        self, team_id: str, key_id: str, private_key_path: str
    ) -> str:
        """
        Generate a developer token for Apple Music API.

        Args:
            team_id: Apple Developer Team ID
            key_id: MusicKit Key ID
            private_key_path: Path to the .p8 private key file

        Returns:
            JWT token string
        """
        try:
            with open(private_key_path, 'r') as f:
                private_key = f.read()

            # Token expires in 6 months (max allowed by Apple)
            expiration = datetime.utcnow() + timedelta(days=180)

            headers = {
                'alg': 'ES256',
                'kid': key_id
            }

            payload = {
                'iss': team_id,
                'iat': int(datetime.utcnow().timestamp()),
                'exp': int(expiration.timestamp())
            }

            token = jwt.encode(payload, private_key, algorithm='ES256', headers=headers)
            logger.info("Successfully generated developer token")
            return token

        except Exception as e:
            logger.error(f"Failed to generate developer token: {e}")
            raise

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        headers = {
            'Authorization': f'Bearer {self.developer_token}',
            'Content-Type': 'application/json'
        }

        if self.user_token:
            headers['Music-User-Token'] = self.user_token

        return headers

    def search_song(self, title: str, artist: str, limit: int = 5) -> Optional[Dict]:
        """
        Search for a song on Apple Music.

        Args:
            title: Song title
            artist: Artist name
            limit: Maximum number of results to return

        Returns:
            Dictionary containing the best match song data, or None if not found
        """
        # Construct search query
        query = f"{title} {artist}".strip()

        params = {
            'term': query,
            'types': 'songs',
            'limit': limit
        }

        try:
            response = requests.get(
                f"{self.BASE_URL}/catalog/us/search",
                headers=self._get_headers(),
                params=params,
                timeout=10
            )

            response.raise_for_status()
            data = response.json()

            # Check if we got results
            if 'results' in data and 'songs' in data['results']:
                songs = data['results']['songs']['data']

                if songs:
                    # Return the best match (first result)
                    best_match = songs[0]
                    logger.info(
                        f"Found song: {best_match['attributes']['name']} by "
                        f"{best_match['attributes']['artistName']}"
                    )
                    return best_match

            logger.warning(f"No results found for: {title} by {artist}")
            return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching for song '{title}' by '{artist}': {e}")
            return None

    def add_song_to_library(self, song_id: str) -> bool:
        """
        Add a song to the user's Apple Music library.

        Args:
            song_id: Apple Music song ID

        Returns:
            True if successful, False otherwise
        """
        if not self.user_token:
            logger.error("Cannot add to library: No user token provided")
            return False

        try:
            payload = {
                'data': [
                    {
                        'id': song_id,
                        'type': 'songs'
                    }
                ]
            }

            response = requests.post(
                f"{self.BASE_URL}/me/library",
                headers=self._get_headers(),
                json=payload,
                params={'ids[songs]': song_id},
                timeout=10
            )

            # 201 Created or 202 Accepted means success
            if response.status_code in [201, 202]:
                logger.info(f"Successfully added song {song_id} to library")
                return True
            else:
                logger.warning(
                    f"Unexpected response when adding song: {response.status_code} - {response.text}"
                )
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Error adding song {song_id} to library: {e}")
            return False

    def add_songs_batch(self, song_ids: List[str]) -> Dict[str, int]:
        """
        Add multiple songs to the library with rate limiting.

        Args:
            song_ids: List of Apple Music song IDs

        Returns:
            Dictionary with counts: {'success': int, 'failed': int}
        """
        results = {'success': 0, 'failed': 0}

        for song_id in song_ids:
            if self.add_song_to_library(song_id):
                results['success'] += 1
            else:
                results['failed'] += 1

            # Rate limiting: wait between requests
            time.sleep(0.5)

        return results

    def search_and_add_song(self, title: str, artist: str) -> tuple[bool, Optional[str]]:
        """
        Search for a song and add it to the library in one operation.

        Args:
            title: Song title
            artist: Artist name

        Returns:
            Tuple of (success: bool, message: str)
        """
        # Search for the song
        song = self.search_song(title, artist)

        if not song:
            return False, "Song not found in Apple Music catalog"

        # Extract song info
        song_id = song['id']
        song_name = song['attributes']['name']
        artist_name = song['attributes']['artistName']

        # Add to library
        if self.add_song_to_library(song_id):
            return True, f"Added '{song_name}' by {artist_name}"
        else:
            return False, f"Found '{song_name}' but failed to add to library"


def test_client():
    """Test function for the Apple Music client"""
    import os
    from dotenv import load_dotenv

    load_dotenv()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Initialize client
    client = AppleMusicClient(
        team_id=os.getenv('APPLE_TEAM_ID'),
        key_id=os.getenv('APPLE_KEY_ID'),
        private_key_path=os.getenv('APPLE_PRIVATE_KEY_PATH'),
        user_token=os.getenv('APPLE_MUSIC_USER_TOKEN')
    )

    # Test search
    print("\nTesting search functionality:")
    result = client.search_song("Blinding Lights", "The Weeknd")
    if result:
        print(f"Found: {result['attributes']['name']} by {result['attributes']['artistName']}")
        print(f"Song ID: {result['id']}")

    # Test search and add (if user token is available)
    if client.user_token:
        print("\nTesting search and add functionality:")
        success, message = client.search_and_add_song("Blinding Lights", "The Weeknd")
        print(f"Result: {message}")


if __name__ == '__main__':
    test_client()
