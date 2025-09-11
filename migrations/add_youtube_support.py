#!/usr/bin/env python3
"""
Database migration script to add YouTube support fields.
Run this script to update the database schema for the YouTube feature.
"""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration():
    """Run database migration to add YouTube support."""
    try:
        # Check if database URL is configured
        if not settings.database_url:
            logger.warning("No database configured. Skipping migration.")
            logger.info("To run migration, set DATABASE_URL environment variable.")
            return

        # Create engine
        engine = create_engine(settings.database_url)

        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()

            try:
                # 1. Create youtube_cards table
                logger.info("Creating youtube_cards table...")
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS youtube_cards (
                        id VARCHAR PRIMARY KEY,
                        title VARCHAR NOT NULL,
                        youtube_video_id VARCHAR(11) NOT NULL,
                        thumbnail_url VARCHAR NOT NULL,
                        duration_seconds INTEGER NOT NULL,
                        start_time_seconds INTEGER,
                        end_time_seconds INTEGER,
                        clip_transcript TEXT NOT NULL,
                        is_active BOOLEAN DEFAULT TRUE NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
                    );
                """))

                # 2. Add new columns to enhancements table
                logger.info("Adding new columns to enhancements table...")

                # Check if columns already exist before adding
                existing_columns = conn.execute(text("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'enhancements'
                """)).fetchall()
                existing_column_names = [col[0] for col in existing_columns]

                # Add prompt_type column
                if 'prompt_type' not in existing_column_names:
                    conn.execute(text("""
                        ALTER TABLE enhancements
                        ADD COLUMN prompt_type VARCHAR DEFAULT 'photo' NOT NULL;
                    """))
                    logger.info("Added prompt_type column")

                # Add prompt_title column
                if 'prompt_title' not in existing_column_names:
                    conn.execute(text("""
                        ALTER TABLE enhancements
                        ADD COLUMN prompt_title VARCHAR;
                    """))
                    logger.info("Added prompt_title column")

                # Add prompt_youtube_thumbnail_url column
                if 'prompt_youtube_thumbnail_url' not in existing_column_names:
                    conn.execute(text("""
                        ALTER TABLE enhancements
                        ADD COLUMN prompt_youtube_thumbnail_url VARCHAR;
                    """))
                    logger.info("Added prompt_youtube_thumbnail_url column")

                # Add source_transcript column
                if 'source_transcript' not in existing_column_names:
                    conn.execute(text("""
                        ALTER TABLE enhancements
                        ADD COLUMN source_transcript TEXT;
                    """))
                    logger.info("Added source_transcript column")

                # Add audio_duration_seconds column
                if 'audio_duration_seconds' not in existing_column_names:
                    conn.execute(text("""
                        ALTER TABLE enhancements
                        ADD COLUMN audio_duration_seconds INTEGER;
                    """))
                    logger.info("Added audio_duration_seconds column")

                # Rename columns if they exist with old names
                if 'original_transcript' in existing_column_names and 'user_transcript' not in existing_column_names:
                    conn.execute(text("""
                        ALTER TABLE enhancements
                        RENAME COLUMN original_transcript TO user_transcript;
                    """))
                    logger.info("Renamed original_transcript to user_transcript")

                if 'photo_base64' in existing_column_names and 'source_photo_base64' not in existing_column_names:
                    conn.execute(text("""
                        ALTER TABLE enhancements
                        RENAME COLUMN photo_base64 TO source_photo_base64;
                    """))
                    logger.info("Renamed photo_base64 to source_photo_base64")

                # 3. Insert sample YouTube cards for testing
                logger.info("Inserting sample YouTube cards...")
                conn.execute(text("""
                    INSERT INTO youtube_cards (
                        id, title, youtube_video_id, thumbnail_url,
                        duration_seconds, start_time_seconds, end_time_seconds,
                        clip_transcript, is_active
                    ) VALUES
                    (
                        'ytc_demo_001',
                        'The Power of Effective Communication',
                        'dQw4w9WgXcQ',
                        'https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg',
                        180,
                        0,
                        180,
                        'In this segment, we explore the fundamental principles of effective communication in professional settings. Clear communication is not just about speaking well, but about ensuring your message is understood and acted upon. We discuss active listening, empathy, and the importance of non-verbal cues.',
                        true
                    ),
                    (
                        'ytc_demo_002',
                        'Leadership Through Storytelling',
                        'jNQXAC9IVRw',
                        'https://i.ytimg.com/vi/jNQXAC9IVRw/maxresdefault.jpg',
                        240,
                        30,
                        270,
                        'Great leaders are great storytellers. This clip examines how narrative techniques can transform dry data into compelling visions that inspire teams. We look at examples from successful CEOs who use stories to communicate strategy, build culture, and drive change.',
                        true
                    )
                    ON CONFLICT (id) DO NOTHING;
                """))

                # Commit transaction
                trans.commit()
                logger.info("✅ Migration completed successfully!")

            except Exception as e:
                trans.rollback()
                logger.error(f"❌ Migration failed: {e}")
                raise

    except Exception as e:
        logger.error(f"❌ Failed to connect to database: {e}")
        raise


if __name__ == "__main__":
    logger.info("Starting YouTube support migration...")
    run_migration()
