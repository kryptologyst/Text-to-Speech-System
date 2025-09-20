# Project 100. Text-to-speech system (Enhanced)
# Description:
# A text-to-speech (TTS) system converts written text into spoken audio. This enhanced version 
# demonstrates both basic pyttsx3 usage and modern TTS capabilities with multiple engines.

# Basic Implementation Using pyttsx3
# Install if not already: pip install pyttsx3

import pyttsx3
import os
from datetime import datetime

def basic_tts_demo():
    """Basic TTS demonstration using pyttsx3"""
    print("🎤 Basic Text-to-Speech Demo")
    print("=" * 40)
    
    # Initialize the TTS engine
    engine = pyttsx3.init()
    
    # Set properties (optional)
    engine.setProperty('rate', 150)       # Speed of speech
    engine.setProperty('volume', 1.0)     # Volume (0.0 to 1.0)
    
    # Choose a voice (optional)
    voices = engine.getProperty('voices')
    print(f"📢 Available voices: {len(voices)}")
    for i, voice in enumerate(voices):
        print(f"  {i}: {voice.name}")
    
    engine.setProperty('voice', voices[0].id)  # Use first voice
    
    # Input text
    text = "Hello! I am your AI assistant. How can I help you today?"
    
    print(f"🗣️  Speaking: {text}")
    
    # Speak the text
    engine.say(text)
    engine.runAndWait()
    
    print("✅ Speech completed!")

def advanced_tts_demo():
    """Advanced TTS with file output and voice selection"""
    print("\n🚀 Advanced Text-to-Speech Demo")
    print("=" * 40)
    
    engine = pyttsx3.init()
    
    # Get available voices
    voices = engine.getProperty('voices')
    
    # Interactive voice selection
    print("Available voices:")
    for i, voice in enumerate(voices):
        print(f"  {i}: {voice.name} ({getattr(voice, 'languages', ['en'])[0]})")
    
    try:
        voice_choice = int(input("Select voice (0-{}): ".format(len(voices)-1)))
        if 0 <= voice_choice < len(voices):
            engine.setProperty('voice', voices[voice_choice].id)
            print(f"✅ Selected voice: {voices[voice_choice].name}")
    except (ValueError, IndexError):
        print("⚠️  Invalid selection, using default voice")
    
    # Customizable settings
    try:
        rate = int(input("Enter speech rate (50-300, default 150): ") or "150")
        engine.setProperty('rate', max(50, min(300, rate)))
    except ValueError:
        engine.setProperty('rate', 150)
    
    try:
        volume = float(input("Enter volume (0.0-1.0, default 1.0): ") or "1.0")
        engine.setProperty('volume', max(0.0, min(1.0, volume)))
    except ValueError:
        engine.setProperty('volume', 1.0)
    
    # Get text input
    text = input("Enter text to convert to speech: ")
    
    if not text.strip():
        text = "Hello! This is a demonstration of the enhanced text-to-speech system."
    
    # Create output directory
    os.makedirs("audio_outputs", exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"audio_outputs/basic_tts_{timestamp}.wav"
    
    print(f"🎵 Saving audio to: {filename}")
    
    # Save to file instead of playing
    engine.save_to_file(text, filename)
    engine.runAndWait()
    
    print(f"✅ Audio saved successfully!")
    print(f"📁 File location: {os.path.abspath(filename)}")
    
    # Ask if user wants to play the file
    play_choice = input("Would you like to play the audio file? (y/n): ").lower()
    if play_choice == 'y':
        try:
            import subprocess
            import platform
            
            system = platform.system()
            if system == "Darwin":  # macOS
                subprocess.run(["afplay", filename])
            elif system == "Windows":
                subprocess.run(["start", filename], shell=True)
            elif system == "Linux":
                subprocess.run(["aplay", filename])
            else:
                print("⚠️  Cannot auto-play audio on this system")
        except Exception as e:
            print(f"⚠️  Could not play audio: {e}")

def show_voice_info():
    """Display detailed voice information"""
    print("\n📋 Voice Information")
    print("=" * 40)
    
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    
    for i, voice in enumerate(voices):
        print(f"\nVoice {i}: {voice.name}")
        print(f"  ID: {voice.id}")
        print(f"  Languages: {getattr(voice, 'languages', ['Unknown'])}")
        print(f"  Gender: {getattr(voice, 'gender', 'Unknown')}")
        print(f"  Age: {getattr(voice, 'age', 'Unknown')}")

if __name__ == "__main__":
    print("🎤 Enhanced Text-to-Speech System")
    print("=" * 50)
    print("This demo shows both basic and advanced TTS capabilities.")
    print("For the full modern system with web interface, run: python modern_tts_system.py")
    print()
    
    while True:
        print("\nChoose an option:")
        print("1. Basic TTS Demo")
        print("2. Advanced TTS Demo")
        print("3. Show Voice Information")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            basic_tts_demo()
        elif choice == '2':
            advanced_tts_demo()
        elif choice == '3':
            show_voice_info()
        elif choice == '4':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")

# 🧠 What This Enhanced Project Demonstrates:
# ✅ Converts text into speech using offline TTS engine
# ✅ Configures speech rate, volume, and voice selection
# ✅ Works offline, no internet required
# ✅ Saves audio to files with timestamps
# ✅ Interactive voice and settings selection
# ✅ Cross-platform audio playback
# ✅ Detailed voice information display
# ✅ User-friendly command-line interface