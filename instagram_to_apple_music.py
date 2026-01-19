#!/usr/bin/env python3
"""
Instagram to Apple Music Song Scraper

This script scrapes songs from an Instagram user's posts and automatically
adds them to your Apple Music library.

Usage:
    python instagram_to_apple_music.py [options]

Options:
    --user USERNAME       Instagram username to scrape (overrides .env)
    --posts N            Number of posts to scrape (default: 100)
    --dry-run            Show what would be added without actually adding
    --output FILE        Save results to CSV file
    --help              Show this help message
"""

import os
import sys
import logging
import argparse
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv

from instagram_scraper import InstagramScraper, Song
from apple_music import AppleMusicClient


class InstagramToAppleMusic:
    """Main orchestrator class for the Instagram to Apple Music pipeline."""

    def __init__(self, config: Dict):
        """
        Initialize the orchestrator.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.dry_run = config.get('dry_run', False)
        self.logger = self._setup_logging(config.get('log_level', 'INFO'))

        # Initialize Instagram scraper
        self.instagram_scraper = InstagramScraper(
            username=config.get('instagram_username'),
            password=config.get('instagram_password')
        )

        # Initialize Apple Music client (if not in dry run mode)
        if not self.dry_run:
            try:
                self.apple_music_client = AppleMusicClient(
                    team_id=config.get('apple_team_id'),
                    key_id=config.get('apple_key_id'),
                    private_key_path=config.get('apple_private_key_path'),
                    developer_token=config.get('apple_developer_token'),
                    user_token=config.get('apple_music_user_token')
                )
            except Exception as e:
                self.logger.error(f"Failed to initialize Apple Music client: {e}")
                sys.exit(1)
        else:
            self.apple_music_client = None
            self.logger.info("Running in DRY RUN mode - no songs will be added")

    def _setup_logging(self, level: str) -> logging.Logger:
        """Setup logging configuration."""
        log_level = getattr(logging, level.upper(), logging.INFO)

        # Create logs directory if it doesn't exist
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)

        # Configure logging
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(
                    log_dir / f"instagram_to_apple_music_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                ),
                logging.StreamHandler()
            ]
        )

        return logging.getLogger(__name__)

    def run(self) -> Dict:
        """
        Run the complete pipeline: scrape Instagram and add songs to Apple Music.

        Returns:
            Dictionary containing execution statistics
        """
        self.logger.info("=" * 80)
        self.logger.info("Starting Instagram to Apple Music Song Scraper")
        self.logger.info("=" * 80)

        target_user = self.config['target_instagram_user']
        max_posts = self.config.get('max_posts', 100)

        # Step 1: Scrape Instagram for songs
        self.logger.info(f"\nStep 1: Scraping songs from @{target_user}")
        self.logger.info("-" * 80)

        songs = self.instagram_scraper.scrape_songs(target_user, max_posts)

        if not songs:
            self.logger.warning("No songs found in Instagram posts!")
            return {
                'songs_found': 0,
                'songs_added': 0,
                'songs_failed': 0,
                'songs_not_found': 0
            }

        self.logger.info(f"\nFound {len(songs)} unique songs")

        # Step 2: Add songs to Apple Music
        self.logger.info(f"\nStep 2: Adding songs to Apple Music")
        self.logger.info("-" * 80)

        results = self._process_songs(songs)

        # Step 3: Generate summary
        self._print_summary(results)

        # Step 4: Save to CSV if requested
        if self.config.get('output_file'):
            self._save_to_csv(results)

        return results['stats']

    def _process_songs(self, songs: List[Song]) -> Dict:
        """
        Process songs and add them to Apple Music.

        Args:
            songs: List of Song objects

        Returns:
            Dictionary containing results and statistics
        """
        results = {
            'added': [],
            'not_found': [],
            'failed': [],
            'stats': {
                'songs_found': len(songs),
                'songs_added': 0,
                'songs_not_found': 0,
                'songs_failed': 0
            }
        }

        for i, song in enumerate(songs, 1):
            self.logger.info(f"\n[{i}/{len(songs)}] Processing: {song}")

            if self.dry_run:
                self.logger.info("  [DRY RUN] Would search and add to Apple Music")
                results['added'].append({
                    'song': song,
                    'message': 'DRY RUN - not actually added'
                })
                results['stats']['songs_added'] += 1
                continue

            try:
                success, message = self.apple_music_client.search_and_add_song(
                    song.title,
                    song.artist
                )

                if success:
                    self.logger.info(f"  ✓ {message}")
                    results['added'].append({
                        'song': song,
                        'message': message
                    })
                    results['stats']['songs_added'] += 1
                elif 'not found' in message.lower():
                    self.logger.warning(f"  ✗ {message}")
                    results['not_found'].append({
                        'song': song,
                        'message': message
                    })
                    results['stats']['songs_not_found'] += 1
                else:
                    self.logger.error(f"  ✗ {message}")
                    results['failed'].append({
                        'song': song,
                        'message': message
                    })
                    results['stats']['songs_failed'] += 1

            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                self.logger.error(f"  ✗ {error_msg}")
                results['failed'].append({
                    'song': song,
                    'message': error_msg
                })
                results['stats']['songs_failed'] += 1

        return results

    def _print_summary(self, results: Dict):
        """Print execution summary."""
        stats = results['stats']

        self.logger.info("\n" + "=" * 80)
        self.logger.info("EXECUTION SUMMARY")
        self.logger.info("=" * 80)
        self.logger.info(f"Total songs found:     {stats['songs_found']}")
        self.logger.info(f"Successfully added:    {stats['songs_added']}")
        self.logger.info(f"Not found on Apple Music: {stats['songs_not_found']}")
        self.logger.info(f"Failed to add:         {stats['songs_failed']}")

        if results['not_found']:
            self.logger.info("\nSongs not found on Apple Music:")
            for item in results['not_found']:
                self.logger.info(f"  - {item['song']}")

        if results['failed']:
            self.logger.info("\nFailed songs:")
            for item in results['failed']:
                self.logger.info(f"  - {item['song']}: {item['message']}")

        self.logger.info("=" * 80)

    def _save_to_csv(self, results: Dict):
        """Save results to CSV file."""
        output_file = self.config['output_file']

        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Song Title', 'Artist', 'Status', 'Message', 'Instagram Post URL'])

                # Write added songs
                for item in results['added']:
                    song = item['song']
                    writer.writerow([
                        song.title,
                        song.artist,
                        'ADDED',
                        item['message'],
                        song.post_url or ''
                    ])

                # Write not found songs
                for item in results['not_found']:
                    song = item['song']
                    writer.writerow([
                        song.title,
                        song.artist,
                        'NOT_FOUND',
                        item['message'],
                        song.post_url or ''
                    ])

                # Write failed songs
                for item in results['failed']:
                    song = item['song']
                    writer.writerow([
                        song.title,
                        song.artist,
                        'FAILED',
                        item['message'],
                        song.post_url or ''
                    ])

            self.logger.info(f"\nResults saved to: {output_file}")

        except Exception as e:
            self.logger.error(f"Failed to save results to CSV: {e}")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Scrape songs from Instagram and add them to Apple Music',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--user',
        help='Instagram username to scrape (overrides .env)'
    )

    parser.add_argument(
        '--posts',
        type=int,
        help='Number of posts to scrape (default: 100)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be added without actually adding'
    )

    parser.add_argument(
        '--output',
        help='Save results to CSV file'
    )

    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Set logging level (default: INFO)'
    )

    return parser.parse_args()


def load_config(args) -> Dict:
    """
    Load configuration from environment and command line arguments.

    Args:
        args: Parsed command line arguments

    Returns:
        Configuration dictionary
    """
    load_dotenv()

    config = {
        'instagram_username': os.getenv('INSTAGRAM_USERNAME'),
        'instagram_password': os.getenv('INSTAGRAM_PASSWORD'),
        'target_instagram_user': args.user or os.getenv('TARGET_INSTAGRAM_USER'),
        'max_posts': args.posts or int(os.getenv('MAX_POSTS', '100')),
        'dry_run': args.dry_run or os.getenv('DRY_RUN', 'false').lower() == 'true',
        'output_file': args.output,
        'log_level': args.log_level or os.getenv('LOG_LEVEL', 'INFO'),
        'apple_team_id': os.getenv('APPLE_TEAM_ID'),
        'apple_key_id': os.getenv('APPLE_KEY_ID'),
        'apple_private_key_path': os.getenv('APPLE_PRIVATE_KEY_PATH'),
        'apple_developer_token': os.getenv('APPLE_DEVELOPER_TOKEN'),
        'apple_music_user_token': os.getenv('APPLE_MUSIC_USER_TOKEN')
    }

    # Validate required configuration
    if not config['target_instagram_user']:
        print("Error: TARGET_INSTAGRAM_USER must be set in .env or provided via --user")
        sys.exit(1)

    return config


def main():
    """Main entry point."""
    args = parse_arguments()
    config = load_config(args)

    try:
        orchestrator = InstagramToAppleMusic(config)
        orchestrator.run()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
