#!/bin/bash

# Modern Text-to-Speech System Startup Script

echo "🎤 Modern Text-to-Speech System"
echo "================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip first."
    exit 1
fi

echo "✅ Python and pip are available"

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "📦 Installing dependencies..."
    pip3 install -r requirements.txt
    echo "✅ Dependencies installed"
else
    echo "⚠️  requirements.txt not found, skipping dependency installation"
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p static templates audio_outputs
echo "✅ Directories created"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from template..."
    if [ -f "env_example.txt" ]; then
        cp env_example.txt .env
        echo "✅ .env file created from template"
        echo "📝 Please edit .env file with your API keys for premium TTS services"
    else
        echo "⚠️  env_example.txt not found, skipping .env creation"
    fi
fi

echo ""
echo "🚀 Starting the Modern Text-to-Speech System..."
echo "🌐 Web interface will be available at: http://localhost:8000"
echo "📱 Press Ctrl+C to stop the server"
echo ""

# Start the application
python3 modern_tts_system.py
