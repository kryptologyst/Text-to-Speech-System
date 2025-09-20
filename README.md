# Text-to-Speech System

A comprehensive, production-ready text-to-speech system supporting multiple TTS engines with a modern web interface.

## Features

### Multiple TTS Engines
- **pyttsx3**: Offline, basic TTS (no internet required)
- **Google TTS (gTTS)**: Online, good quality, free
- **OpenAI TTS**: Premium quality, natural-sounding voices
- **Azure Speech Services**: Enterprise-grade TTS with neural voices
- **Coqui TTS**: AI-powered, supports voice cloning

### Advanced Features
- **Voice Customization**: Adjust speech rate, volume, and voice selection
- **Database Storage**: SQLite database for TTS history and settings
- **Modern Web UI**: Responsive interface with real-time audio playback
- **API Endpoints**: RESTful API for integration with other applications
- **Docker Support**: Easy deployment with Docker and Docker Compose
- **Audio Processing**: Support for various audio formats and durations

### Web Interface
- Clean, modern design
- Real-time voice selection based on engine
- Audio player with controls
- Voice history and management
- Responsive design for mobile and desktop

## Quick Start

### Prerequisites
- Python 3.8+
- pip or conda
- (Optional) Docker and Docker Compose

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd 0100_Text-to-speech_system
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables** (Optional)
   ```bash
   cp env_example.txt .env
   # Edit .env with your API keys for premium services
   ```

4. **Run the application**
   ```bash
   python modern_tts_system.py
   ```

5. **Access the web interface**
   Open your browser and go to `http://localhost:8000`

### Docker Deployment

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

2. **Or build and run manually**
   ```bash
   docker build -t modern-tts .
   docker run -p 8000:8000 modern-tts
   ```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# OpenAI API Configuration (Optional)
OPENAI_API_KEY=your_openai_api_key_here

# Azure Speech Services Configuration (Optional)
AZURE_SPEECH_KEY=your_azure_speech_key_here
AZURE_SPEECH_REGION=your_azure_region_here

# Database Configuration
DATABASE_URL=sqlite:///./tts_database.db

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=True
```

### API Keys Setup

#### OpenAI TTS (Premium)
1. Get API key from [OpenAI Platform](https://platform.openai.com/)
2. Add to `.env`: `OPENAI_API_KEY=your_key_here`

#### Azure Speech Services (Premium)
1. Create Azure Speech resource
2. Get key and region from Azure portal
3. Add to `.env`:
   ```env
   AZURE_SPEECH_KEY=your_key_here
   AZURE_SPEECH_REGION=your_region_here
   ```

## API Documentation

### Endpoints

#### `GET /`
- **Description**: Web interface
- **Response**: HTML page with TTS interface

#### `GET /api/voices`
- **Description**: Get available voices from all engines
- **Response**: List of voice objects
```json
[
  {
    "engine": "pyttsx3",
    "name": "Voice 0",
    "language": "en",
    "gender": "unknown"
  }
]
```

#### `POST /api/synthesize`
- **Description**: Generate speech from text
- **Request Body**:
```json
{
  "text": "Hello world",
  "voice_engine": "pyttsx3",
  "voice_name": "Voice 0",
  "rate": 150,
  "volume": 1.0,
  "language": "en"
}
```
- **Response**:
```json
{
  "success": true,
  "audio_file_path": "/path/to/audio.wav",
  "duration": 2.5,
  "message": "Speech synthesized successfully"
}
```

#### `GET /api/history`
- **Description**: Get TTS generation history
- **Response**: List of recent TTS records

## Architecture

### Project Structure
```
0100_Text-to-speech_system/
├── modern_tts_system.py      # Main application
├── 0100.py                   # Original simple implementation
├── requirements.txt          # Python dependencies
├── Dockerfile               # Docker configuration
├── docker-compose.yml       # Docker Compose setup
├── env_example.txt          # Environment variables template
├── README.md                # This file
├── static/                  # Static files (CSS, JS)
├── templates/               # HTML templates
└── audio_outputs/          # Generated audio files
```

### Database Schema
```sql
CREATE TABLE tts_records (
    id INTEGER PRIMARY KEY,
    text TEXT NOT NULL,
    voice_engine VARCHAR(50) NOT NULL,
    voice_name VARCHAR(100),
    audio_file_path VARCHAR(500),
    duration FLOAT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    settings TEXT  -- JSON string for voice settings
);
```

## Usage Examples

### Python API Usage
```python
import requests

# Generate speech
response = requests.post('http://localhost:8000/api/synthesize', json={
    'text': 'Hello, this is a test of the TTS system.',
    'voice_engine': 'pyttsx3',
    'rate': 150,
    'volume': 1.0
})

if response.json()['success']:
    print(f"Audio saved to: {response.json()['audio_file_path']}")
```

### Command Line Usage
```bash
# Using curl
curl -X POST "http://localhost:8000/api/synthesize" \
     -H "Content-Type: application/json" \
     -d '{"text": "Hello world", "voice_engine": "pyttsx3"}'
```

## 🛠️ Development

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black modern_tts_system.py
flake8 modern_tts_system.py
```

### Adding New TTS Engines

1. Add engine initialization in `setup_engines()`
2. Implement synthesis method `_synthesize_<engine>()`
3. Add voice information in `get_available_voices()`
4. Update the web interface voice selection

## Performance

### Benchmarks
- **pyttsx3**: ~0.5s for 10 words (offline)
- **gTTS**: ~2s for 10 words (online)
- **OpenAI TTS**: ~1s for 10 words (premium)
- **Azure Speech**: ~1.5s for 10 words (premium)
- **Coqui TTS**: ~3s for 10 words (AI processing)

### Optimization Tips
- Use pyttsx3 for offline applications
- Cache frequently used audio files
- Implement audio compression for storage
- Use async processing for multiple requests

## Security Considerations

- API keys should be stored securely
- Implement rate limiting for production use
- Validate input text to prevent injection attacks
- Use HTTPS in production environments
- Implement user authentication if needed

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [pyttsx3](https://github.com/nateshmbhat/pyttsx3) - Cross-platform TTS library
- [gTTS](https://github.com/pndurette/gTTS) - Google Text-to-Speech
- [OpenAI](https://openai.com/) - Advanced TTS models
- [Azure Speech Services](https://azure.microsoft.com/en-us/services/cognitive-services/speech-services/) - Enterprise TTS
- [Coqui TTS](https://github.com/coqui-ai/TTS) - Open-source TTS toolkit
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework


# Text-to-Speech-System
