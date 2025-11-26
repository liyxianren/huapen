"""
Main entry point for Zeabur deployment
Updated: 2025-11-26 - Trigger Zeabur redeploy
"""
from app_sqlite import app

if __name__ == '__main__':
    app.run()
