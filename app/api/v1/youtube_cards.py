"""
YouTube cards endpoint for fetching curated video clips.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from app.core.database import get_db_session
from app.core.auth import get_current_user_optional
from app.models.youtube_card import YouTubeCard
from app.schemas.youtube import YouTubeCard as YouTubeCardSchema


logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/youtube-cards", response_model=List[YouTubeCardSchema])
async def get_youtube_cards(
    current_user: dict = Depends(get_current_user_optional),
    db: Session = Depends(get_db_session)
) -> List[YouTubeCardSchema]:
    """
    Get available YouTube practice cards.

    Returns a list of curated YouTube video clips for users to practice communication skills.
    Only returns active cards.
    """
    try:
        # Query only active YouTube cards
        cards = db.query(YouTubeCard).filter_by(is_active=True).all()

        # Convert to Pydantic schemas
        return [
            YouTubeCardSchema(
                id=card.id,
                title=card.title,
                youtube_video_id=card.youtube_video_id,
                thumbnail_url=card.thumbnail_url,
                duration_seconds=card.duration_seconds,
                start_time_seconds=card.start_time_seconds,
                end_time_seconds=card.end_time_seconds,
                clip_transcript=card.clip_transcript
            )
            for card in cards
        ]
    except Exception as e:
        logger.error(f"Error fetching YouTube cards: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch YouTube cards"
        )
