#!/usr/bin/env python3
"""
Test script for AIOM4B conversion functionality.
This script demonstrates how to use the API programmatically.
"""

import asyncio
import requests
import time
from pathlib import Path

API_BASE_URL = "http://localhost:8000/api/v1"

def test_api():
    """Test the AIOM4B API endpoints."""
    
    print("🧪 Testing AIOM4B API...")
    
    # Test 1: Health check
    print("\n1. Testing health check...")
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("✅ Health check passed")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return
    
    # Test 2: List folders
    print("\n2. Testing folder listing...")
    try:
        response = requests.get(f"{API_BASE_URL}/folders")
        if response.status_code == 200:
            folders = response.json()
            print(f"✅ Found {len(folders)} folders")
            for folder in folders:
                print(f"   📁 {folder['path']} ({folder['mp3_count']} files, {folder['total_size_mb']:.2f} MB)")
        else:
            print(f"❌ Folder listing failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Folder listing failed: {e}")
    
    # Test 3: List jobs
    print("\n3. Testing job listing...")
    try:
        response = requests.get(f"{API_BASE_URL}/jobs")
        if response.status_code == 200:
            jobs = response.json()
            print(f"✅ Found {len(jobs)} active jobs")
        else:
            print(f"❌ Job listing failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Job listing failed: {e}")
    
    print("\n🎯 API Testing Complete!")
    print("\n📝 Note: To test conversion, you need actual MP3 files.")
    print("   Place MP3 files in the 'source/' directory and try the conversion.")

def create_sample_mp3_info():
    """Create information about how to get sample MP3 files."""
    
    print("\n📋 How to Test with Real MP3 Files:")
    print("=" * 50)
    print("1. Download sample MP3 files from:")
    print("   - https://www.soundjay.com/")
    print("   - https://freesound.org/")
    print("   - Or use your own MP3 audiobooks")
    print()
    print("2. Create a folder in 'source/' directory:")
    print("   mkdir source/my_audiobook")
    print()
    print("3. Copy MP3 files to the folder:")
    print("   cp *.mp3 source/my_audiobook/")
    print()
    print("4. Use the web interface at http://localhost:3000")
    print("   or the API to start conversion")
    print()
    print("5. Example API call:")
    print("   curl -X POST http://localhost:8000/api/v1/convert \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{\"source_folders\": [\"source/my_audiobook\"]}'")

if __name__ == "__main__":
    test_api()
    create_sample_mp3_info()
