"""
Unit tests for database utilities and configuration.
"""
import pytest
import os
from unittest.mock import patch, MagicMock
from app.core.database import get_database_url, create_database_engine, create_tables


@pytest.mark.unit
class TestDatabaseUtilities:
    """Test database utility functions."""
    
    @patch.dict(os.environ, {"DATABASE_URL": "postgres://user:pass@localhost/db"})
    def test_get_database_url_from_env(self):
        """Test getting database URL from environment variable."""
        url = get_database_url()
        assert url == "postgresql://user:pass@localhost/db"  # postgres:// converted to postgresql://
    
    @patch.dict(os.environ, {"DATABASE_URL": "postgresql://user:pass@localhost/db"})
    def test_get_database_url_already_postgresql(self):
        """Test database URL that already uses postgresql://."""
        url = get_database_url()
        assert url == "postgresql://user:pass@localhost/db"  # No change needed
    
    @patch.dict(os.environ, {}, clear=True)
    def test_get_database_url_missing(self):
        """Test error when DATABASE_URL is not set."""
        with pytest.raises(ValueError, match="DATABASE_URL environment variable is required"):
            get_database_url()
    
    @patch('app.core.database.get_database_url')
    @patch('app.core.database.create_engine')
    def test_create_database_engine(self, mock_create_engine, mock_get_url):
        """Test creating database engine."""
        mock_get_url.return_value = "postgresql://test"
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        
        engine = create_database_engine()
        
        mock_get_url.assert_called_once()
        mock_create_engine.assert_called_once()
        assert engine == mock_engine
    
    @patch('app.core.database.get_database_url')
    @patch('app.core.database.create_engine')
    @patch('app.core.database.Base')
    def test_create_tables_success(self, mock_base, mock_create_engine, mock_get_url):
        """Test successful table creation."""
        mock_get_url.return_value = "postgresql://test"
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_metadata = MagicMock()
        mock_base.metadata = mock_metadata
        
        # Should not raise an exception
        create_tables()
        
        mock_get_url.assert_called_once()
        mock_create_engine.assert_called_once_with("postgresql://test")
        mock_metadata.create_all.assert_called_once_with(bind=mock_engine)
    
    @patch('app.core.database.get_database_url')
    def test_create_tables_database_error(self, mock_get_url):
        """Test table creation with database error."""
        mock_get_url.side_effect = ValueError("Database connection failed")
        
        with pytest.raises(ValueError, match="Database connection failed"):
            create_tables()
    
    @patch.dict(os.environ, {"DATABASE_URL": "sqlite:///test.db"})
    @patch('app.core.database.create_engine')
    def test_get_db_session_generator(self, mock_create_engine):
        """Test database session generator."""
        from app.core.database import get_db_session
        
        # Mock session and engine
        mock_session = MagicMock()
        mock_session_local = MagicMock(return_value=mock_session)
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        
        with patch('app.core.database.sessionmaker', return_value=mock_session_local):
            # Test the generator
            session_gen = get_db_session()
            session = next(session_gen)
            
            assert session == mock_session
            mock_session_local.assert_called_once()
            
            # Test cleanup when generator is closed
            try:
                next(session_gen)
            except StopIteration:
                pass
            
            mock_session.close.assert_called_once()
    
    @patch.dict(os.environ, {}, clear=True)
    def test_get_db_session_no_database_url(self):
        """Test database session when DATABASE_URL is not set."""
        from app.core.database import get_db_session
        
        session_gen = get_db_session()
        
        with pytest.raises(RuntimeError, match="Database not configured"):
            next(session_gen)