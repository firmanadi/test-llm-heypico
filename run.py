#!/usr/bin/env python3
"""
Quick start script for LLM Location Assistant
"""

import os
import sys
from pathlib import Path

def check_requirements():
    """Check if all requirements are met"""
    print("🔍 Checking requirements...")

    # Check .env file
    if not Path(".env").exists():
        print("⚠️  .env file not found!")
        print("📝 Creating .env from .env.example...")

        if Path(".env.example").exists():
            import shutil
            shutil.copy(".env.example", ".env")
            print("✅ Created .env file")
            print("⚙️  Please edit .env and add your Google Maps API key")
            return False
        else:
            print("❌ .env.example not found!")
            return False

    # Check if Google Maps API key is set
    from dotenv import load_dotenv
    load_dotenv()

    if not os.getenv("GOOGLE_MAPS_API_KEY"):
        print("⚠️  GOOGLE_MAPS_API_KEY not set in .env")
        print("⚙️  Please add your Google Maps API key to .env file")
        return False

    print("✅ Configuration looks good!")
    return True

def main():
    """Run the application"""
    print("🚀 Starting LLM Location Assistant...")
    print()

    # Check requirements
    if not check_requirements():
        print()
        print("❌ Please fix the configuration issues above and try again")
        sys.exit(1)

    # Import and run
    print()
    print("📡 Starting server...")
    print("🌐 Frontend: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print()
    print("Press Ctrl+C to stop")
    print("-" * 50)
    print()

    import uvicorn
    from app.config import settings

    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG
    )

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
