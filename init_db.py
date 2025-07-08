#!/usr/bin/env python3
"""Initialize database tables for production deployment"""

from app import app, db

def init_database():
    """Initialize database with all tables"""
    with app.app_context():
        db.create_all()
        print("Database tables created successfully")

if __name__ == '__main__':
    init_database() 