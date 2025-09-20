#!/usr/bin/env python3
"""
Test script for Modern Text-to-Speech System
"""

import asyncio
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

from modern_tts_system import ModernTTSSystem, TTSRequest

async def test_tts_engines():
    """Test all available TTS engines"""
    print("🧪 Testing Modern Text-to-Speech System")
    print("=" * 50)
    
    # Initialize TTS system
    tts_system = ModernTTSSystem()
    
    # Test text
    test_text = "Hello! This is a test of the modern text-to-speech system."
    
    # Get available voices
    print("\n📢 Available Voices:")
    voices = tts_system.get_available_voices()
    for voice in voices:
        print(f"  • {voice.engine}: {voice.name} ({voice.language})")
    
    # Test each available engine
    engines_to_test = ['pyttsx3', 'gtts']  # Start with free engines
    
    # Add premium engines if API keys are available
    if 'openai' in tts_system.engines:
        engines_to_test.append('openai')
    if 'azure' in tts_system.engines:
        engines_to_test.append('azure')
    if 'coqui' in tts_system.engines:
        engines_to_test.append('coqui')
    
    print(f"\n🎤 Testing {len(engines_to_test)} engines...")
    
    for engine in engines_to_test:
        print(f"\n🔧 Testing {engine.upper()} engine:")
        try:
            request = TTSRequest(
                text=test_text,
                voice_engine=engine,
                rate=150,
                volume=1.0
            )
            
            response = await tts_system.synthesize_speech(request)
            
            if response.success:
                print(f"  ✅ Success! Audio saved to: {response.audio_file_path}")
                print(f"  ⏱️  Duration: {response.duration:.2f} seconds")
                print(f"  💬 Message: {response.message}")
                
                # Save to database
                tts_system.save_to_database(request, response)
            else:
                print(f"  ❌ Failed: {response.message}")
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
    
    print("\n🎉 Testing completed!")
    print("\n📊 Database Records:")
    
    # Show database records
    try:
        from modern_tts_system import SessionLocal, TTSRecord
        db = SessionLocal()
        records = db.query(TTSRecord).order_by(TTSRecord.created_at.desc()).limit(5).all()
        db.close()
        
        for record in records:
            print(f"  • {record.voice_engine}: {record.text[:30]}... ({record.duration:.2f}s)")
    except Exception as e:
        print(f"  Could not retrieve database records: {e}")

def test_web_server():
    """Test if the web server can start"""
    print("\n🌐 Testing Web Server...")
    try:
        import uvicorn
        from modern_tts_system import app
        
        print("  ✅ FastAPI app loaded successfully")
        print("  🌍 Server can be started with: uvicorn modern_tts_system:app --host 0.0.0.0 --port 8000")
        print("  📱 Web interface will be available at: http://localhost:8000")
        
    except Exception as e:
        print(f"  ❌ Web server test failed: {e}")

if __name__ == "__main__":
    print("🚀 Modern Text-to-Speech System Test Suite")
    print("=" * 60)
    
    # Run async tests
    asyncio.run(test_tts_engines())
    
    # Test web server
    test_web_server()
    
    print("\n✨ All tests completed!")
    print("\n📖 Next steps:")
    print("  1. Run 'python modern_tts_system.py' to start the web server")
    print("  2. Open http://localhost:8000 in your browser")
    print("  3. Try different TTS engines and voices")
    print("  4. Check the generated audio files in the 'audio_outputs' directory")
