"""
Launcher script for AI-Powered Video Lecture Generator
"""
import sys
import uvicorn

# Ensure utf-8 encoding on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

if __name__ == "__main__":
    print("=" * 60)
    print("Starting AI-Powered Video Lecture Generator...")
    print("Local Server URL: http://127.0.0.1:8000")
    print("=" * 60)
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=False)
