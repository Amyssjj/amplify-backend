"""
Unit tests for database models.
"""
import pytest
from datetime import datetime
from app.models.enhancement import Enhancement, AudioStatusEnum, PromptTypeEnum
from app.models.user import User


@pytest.mark.unit
class TestEnhancementModel:
    """Test Enhancement database model."""

    def test_enhancement_creation(self, db_session, sample_enhancement_data, sample_user_data):
        """Test creating an Enhancement record."""
        # Create user first
        user = User(**sample_user_data)
        db_session.add(user)
        db_session.commit()

        # Create enhancement
        enhancement = Enhancement(**sample_enhancement_data)
        db_session.add(enhancement)
        db_session.commit()

        assert enhancement.enhancement_id == "enh_test123"
        assert enhancement.user_id == "usr_test123"
        assert enhancement.user_transcript == "Original story text"
        assert enhancement.enhanced_transcript == "Enhanced story text with improvements"
        assert enhancement.insights == {"plot": "Good story structure", "character": "Strong protagonist"}
        assert enhancement.audio_status == AudioStatusEnum.NOT_GENERATED
        assert enhancement.language == "en"
        assert enhancement.prompt_type.value == "photo"
        assert enhancement.source_photo_base64 == "fake_base64_image_data"
        assert isinstance(enhancement.created_at, datetime)

    def test_enhancement_audio_status_enum(self):
        """Test AudioStatus enum values."""
        assert AudioStatusEnum.NOT_GENERATED.value == "not_generated"
        assert AudioStatusEnum.READY.value == "ready"

    def test_enhancement_relationships(self, db_session, sample_enhancement_data, sample_user_data):
        """Test Enhancement-User relationship."""
        # Create user
        user = User(**sample_user_data)
        db_session.add(user)
        db_session.commit()

        # Create enhancement
        enhancement = Enhancement(**sample_enhancement_data)
        db_session.add(enhancement)
        db_session.commit()

        # Test relationship
        assert enhancement.user.email == "test@example.com"
        assert len(user.enhancements) == 1
        assert user.enhancements[0].enhancement_id == "enh_test123"


@pytest.mark.unit
class TestUserModel:
    """Test User database model."""

    def test_user_creation(self, db_session, sample_user_data):
        """Test creating a User record."""
        user = User(**sample_user_data)
        db_session.add(user)
        db_session.commit()

        assert user.user_id == "usr_test123"
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.picture == "https://example.com/avatar.jpg"
        assert user.google_id == "google_123456"
        assert isinstance(user.created_at, datetime)
        assert user.last_login is None

    def test_user_unique_constraints(self, db_session, sample_user_data):
        """Test unique constraints on email and google_id."""
        # Create first user
        user1 = User(**sample_user_data)
        db_session.add(user1)
        db_session.commit()

        # Try to create user with same email
        user2_data = sample_user_data.copy()
        user2_data["user_id"] = "usr_test456"
        user2_data["google_id"] = "google_789"

        user2 = User(**user2_data)
        db_session.add(user2)

        with pytest.raises(Exception):  # Should fail due to unique email constraint
            db_session.commit()

        db_session.rollback()

        # Try to create user with same google_id
        user3_data = sample_user_data.copy()
        user3_data["user_id"] = "usr_test789"
        user3_data["email"] = "different@example.com"

        user3 = User(**user3_data)
        db_session.add(user3)

        with pytest.raises(Exception):  # Should fail due to unique google_id constraint
            db_session.commit()

    def test_user_enhancement_relationship(self, db_session, sample_user_data):
        """Test User-Enhancement relationship."""
        user = User(**sample_user_data)
        db_session.add(user)
        db_session.commit()

        # Initially no enhancements
        assert len(user.enhancements) == 0

        # Add enhancement
        enhancement = Enhancement(
            enhancement_id="enh_test456",
            user_id=user.user_id,
            prompt_type=PromptTypeEnum.PHOTO,
            source_photo_base64="test_photo_data",
            user_transcript="Test transcript",
            enhanced_transcript="Enhanced test transcript",
            insights={"test": "insight"},
            audio_status=AudioStatusEnum.NOT_GENERATED,
            language="en"
        )
        db_session.add(enhancement)
        db_session.commit()

        # Check relationship
        db_session.refresh(user)
        assert len(user.enhancements) == 1
        assert user.enhancements[0].enhancement_id == "enh_test456"
