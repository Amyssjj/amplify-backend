#!/usr/bin/env python3
"""
Database initialization script for Replit deployment.
Run this once to create tables before starting the application.
"""
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import create_tables

if __name__ == "__main__":
    print("🚀 Initializing Amplify Backend database...")
    
    try:
        create_tables()
        print("✅ Database initialization completed successfully!")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)