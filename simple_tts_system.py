import os
import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path
import json

# Core TTS Libraries (basic)
import pyttsx3

# Database
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Web Framework
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Configuration
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
Base = declarative_base()

class TTSRecord(Base):
    __tablename__ = "tts_records"
    
    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    voice_engine = Column(String(50), nullable=False)
    voice_name = Column(String(100))
    audio_file_path = Column(String(500))
    duration = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    settings = Column(Text)  # JSON string for voice settings

# Database connection
DATABASE_URL = "sqlite:///./tts_database.db"
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Pydantic models
class TTSRequest(BaseModel):
    text: str
    voice_engine: str = "pyttsx3"
    voice_name: Optional[str] = None
    rate: Optional[int] = 150
    volume: Optional[float] = 1.0
    language: Optional[str] = "en"

class TTSResponse(BaseModel):
    success: bool
    audio_file_path: Optional[str] = None
    duration: Optional[float] = None
    message: str

class VoiceInfo(BaseModel):
    engine: str
    name: str
    language: str
    gender: Optional[str] = None

class ModernTTSSystem:
    def __init__(self):
        self.engines = {}
        self.setup_engines()
        self.audio_dir = Path("audio_outputs")
        self.audio_dir.mkdir(exist_ok=True)
        
    def setup_engines(self):
        """Initialize all available TTS engines"""
        try:
            # pyttsx3 (offline, basic)
            self.engines['pyttsx3'] = pyttsx3.init()
            logger.info("pyttsx3 engine initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize pyttsx3: {e}")
    
    def get_available_voices(self) -> List[VoiceInfo]:
        """Get list of available voices from all engines"""
        voices = []
        
        # pyttsx3 voices
        if 'pyttsx3' in self.engines:
            try:
                pyttsx3_voices = self.engines['pyttsx3'].getProperty('voices')
                for i, voice in enumerate(pyttsx3_voices):
                    voices.append(VoiceInfo(
                        engine="pyttsx3",
                        name=voice.name or f"Voice {i}",
                        language=getattr(voice, 'languages', ['en'])[0] if hasattr(voice, 'languages') else 'en',
                        gender=getattr(voice, 'gender', 'unknown')
                    ))
            except Exception as e:
                logger.warning(f"Failed to get pyttsx3 voices: {e}")
        
        return voices
    
    async def synthesize_speech(self, request: TTSRequest) -> TTSResponse:
        """Synthesize speech using the specified engine"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_filename = f"tts_{request.voice_engine}_{timestamp}.wav"
            audio_path = self.audio_dir / audio_filename
            
            if request.voice_engine == "pyttsx3":
                return await self._synthesize_pyttsx3(request, audio_path)
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported engine: {request.voice_engine}")
                
        except Exception as e:
            logger.error(f"TTS synthesis failed: {e}")
            return TTSResponse(success=False, message=str(e))
    
    async def _synthesize_pyttsx3(self, request: TTSRequest, audio_path: Path) -> TTSResponse:
        """Synthesize using pyttsx3"""
        try:
            engine = self.engines['pyttsx3']
            
            # Set properties
            engine.setProperty('rate', request.rate or 150)
            engine.setProperty('volume', request.volume or 1.0)
            
            # Set voice if specified
            if request.voice_name:
                voices = engine.getProperty('voices')
                for voice in voices:
                    if request.voice_name in voice.name:
                        engine.setProperty('voice', voice.id)
                        break
            
            # Save to file
            engine.save_to_file(request.text, str(audio_path))
            engine.runAndWait()
            
            # Get duration (simplified)
            duration = len(request.text) * 0.1  # Rough estimate
            
            return TTSResponse(
                success=True,
                audio_file_path=str(audio_path),
                duration=duration,
                message="Speech synthesized successfully with pyttsx3"
            )
        except Exception as e:
            raise Exception(f"pyttsx3 synthesis failed: {e}")
    
    def save_to_database(self, request: TTSRequest, response: TTSResponse):
        """Save TTS request and response to database"""
        try:
            db = SessionLocal()
            record = TTSRecord(
                text=request.text,
                voice_engine=request.voice_engine,
                voice_name=request.voice_name,
                audio_file_path=response.audio_file_path,
                duration=response.duration,
                settings=json.dumps({
                    "rate": request.rate,
                    "volume": request.volume,
                    "language": request.language
                })
            )
            db.add(record)
            db.commit()
            db.close()
        except Exception as e:
            logger.error(f"Failed to save to database: {e}")

# Initialize TTS system
tts_system = ModernTTSSystem()

# FastAPI app
app = FastAPI(title="Modern Text-to-Speech System", version="2.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main web interface"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Modern Text-to-Speech System</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
            .container { background: rgba(255,255,255,0.1); padding: 30px; border-radius: 15px; backdrop-filter: blur(10px); }
            h1 { text-align: center; margin-bottom: 30px; }
            textarea { width: 100%; height: 120px; margin: 15px 0; padding: 15px; border: none; border-radius: 10px; font-size: 16px; }
            select, input { margin: 8px; padding: 12px; border: none; border-radius: 8px; font-size: 14px; }
            button { background: #ff6b6b; color: white; padding: 15px 30px; border: none; border-radius: 10px; cursor: pointer; font-size: 16px; font-weight: bold; }
            button:hover { background: #ff5252; transform: translateY(-2px); }
            .audio-player { margin: 25px 0; }
            .voice-info { background: rgba(255,255,255,0.1); padding: 20px; margin: 15px 0; border-radius: 10px; }
            .status { margin: 15px 0; padding: 10px; border-radius: 5px; }
            .success { background: rgba(76, 175, 80, 0.3); }
            .error { background: rgba(244, 67, 54, 0.3); }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎤 Modern Text-to-Speech System</h1>
            
            <form id="ttsForm">
                <div>
                    <label for="text"><strong>Text to convert:</strong></label>
                    <textarea id="text" placeholder="Enter your text here..." required></textarea>
                </div>
                
                <div>
                    <label for="engine"><strong>TTS Engine:</strong></label>
                    <select id="engine">
                        <option value="pyttsx3">pyttsx3 (Offline)</option>
                    </select>
                </div>
                
                <div>
                    <label for="voice"><strong>Voice:</strong></label>
                    <select id="voice">
                        <option value="">Default</option>
                    </select>
                </div>
                
                <div>
                    <label for="rate"><strong>Speech Rate:</strong></label>
                    <input type="range" id="rate" min="50" max="300" value="150">
                    <span id="rateValue">150</span>
                </div>
                
                <div>
                    <label for="volume"><strong>Volume:</strong></label>
                    <input type="range" id="volume" min="0" max="1" step="0.1" value="1">
                    <span id="volumeValue">1.0</span>
                </div>
                
                <button type="submit">🎵 Generate Speech</button>
            </form>
            
            <div id="result" class="audio-player" style="display: none;">
                <h3>Generated Audio:</h3>
                <audio controls id="audioPlayer" style="width: 100%;"></audio>
                <div id="status" class="status"></div>
            </div>
            
            <div id="voices" class="voice-info">
                <h3>Available Voices:</h3>
                <div id="voiceList"></div>
            </div>
        </div>
        
        <script>
            let voices = [];
            
            // Load available voices
            async function loadVoices() {
                try {
                    const response = await fetch('/api/voices');
                    voices = await response.json();
                    updateVoiceSelect();
                    displayVoiceList();
                } catch (error) {
                    console.error('Failed to load voices:', error);
                }
            }
            
            function updateVoiceSelect() {
                const voiceSelect = document.getElementById('voice');
                const engine = document.getElementById('engine').value;
                
                voiceSelect.innerHTML = '<option value="">Default</option>';
                
                voices.filter(v => v.engine === engine).forEach(voice => {
                    const option = document.createElement('option');
                    option.value = voice.name;
                    option.textContent = `${voice.name} (${voice.language})`;
                    voiceSelect.appendChild(option);
                });
            }
            
            function displayVoiceList() {
                const voiceList = document.getElementById('voiceList');
                voiceList.innerHTML = '';
                
                const engines = [...new Set(voices.map(v => v.engine))];
                engines.forEach(engine => {
                    const engineDiv = document.createElement('div');
                    engineDiv.innerHTML = `<h4>${engine.toUpperCase()}</h4>`;
                    
                    const engineVoices = voices.filter(v => v.engine === engine);
                    engineVoices.forEach(voice => {
                        const voiceDiv = document.createElement('div');
                        voiceDiv.innerHTML = `• ${voice.name} (${voice.language}) ${voice.gender ? `- ${voice.gender}` : ''}`;
                        engineDiv.appendChild(voiceDiv);
                    });
                    
                    voiceList.appendChild(engineDiv);
                });
            }
            
            // Update range value displays
            document.getElementById('rate').addEventListener('input', function() {
                document.getElementById('rateValue').textContent = this.value;
            });
            
            document.getElementById('volume').addEventListener('input', function() {
                document.getElementById('volumeValue').textContent = this.value;
            });
            
            // Update voice select when engine changes
            document.getElementById('engine').addEventListener('change', updateVoiceSelect);
            
            // Handle form submission
            document.getElementById('ttsForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const formData = {
                    text: document.getElementById('text').value,
                    voice_engine: document.getElementById('engine').value,
                    voice_name: document.getElementById('voice').value || null,
                    rate: parseInt(document.getElementById('rate').value),
                    volume: parseFloat(document.getElementById('volume').value),
                    language: 'en'
                };
                
                try {
                    const response = await fetch('/api/synthesize', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(formData)
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        document.getElementById('audioPlayer').src = `/static/${result.audio_file_path.split('/').pop()}`;
                        document.getElementById('status').textContent = result.message;
                        document.getElementById('status').className = 'status success';
                        document.getElementById('result').style.display = 'block';
                    } else {
                        document.getElementById('status').textContent = `Error: ${result.message}`;
                        document.getElementById('status').className = 'status error';
                        document.getElementById('result').style.display = 'block';
                    }
                } catch (error) {
                    document.getElementById('status').textContent = `Error: ${error.message}`;
                    document.getElementById('status').className = 'status error';
                    document.getElementById('result').style.display = 'block';
                }
            });
            
            // Load voices on page load
            loadVoices();
        </script>
    </body>
    </html>
    """

@app.get("/api/voices")
async def get_voices():
    """Get available voices from all engines"""
    return tts_system.get_available_voices()

@app.post("/api/synthesize", response_model=TTSResponse)
async def synthesize_speech(request: TTSRequest):
    """Synthesize speech using the specified engine"""
    response = await tts_system.synthesize_speech(request)
    
    if response.success:
        tts_system.save_to_database(request, response)
    
    return response

@app.get("/api/history")
async def get_history():
    """Get TTS generation history"""
    try:
        db = SessionLocal()
        records = db.query(TTSRecord).order_by(TTSRecord.created_at.desc()).limit(50).all()
        db.close()
        
        return [
            {
                "id": record.id,
                "text": record.text[:100] + "..." if len(record.text) > 100 else record.text,
                "voice_engine": record.voice_engine,
                "voice_name": record.voice_name,
                "duration": record.duration,
                "created_at": record.created_at.isoformat()
            }
            for record in records
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
