import os
import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path
import json

# Core TTS Libraries
import pyttsx3
from gtts import gTTS
import azure.cognitiveservices.speech as speechsdk
from openai import OpenAI
import torch
from TTS.api import TTS

# Database
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Web Framework
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

# Audio Processing
from pydub import AudioSegment
import soundfile as sf
import numpy as np

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
            
        try:
            # OpenAI TTS (high quality, requires API key)
            if os.getenv("OPENAI_API_KEY"):
                self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                self.engines['openai'] = self.openai_client
                logger.info("OpenAI TTS engine initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI TTS: {e}")
            
        try:
            # Azure Speech Services (high quality, requires API key)
            if os.getenv("AZURE_SPEECH_KEY") and os.getenv("AZURE_SPEECH_REGION"):
                self.azure_speech_key = os.getenv("AZURE_SPEECH_KEY")
                self.azure_speech_region = os.getenv("AZURE_SPEECH_REGION")
                self.engines['azure'] = True
                logger.info("Azure Speech engine initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Azure Speech: {e}")
            
        try:
            # Coqui TTS (offline, high quality, supports voice cloning)
            if torch.cuda.is_available():
                self.tts_coqui = TTS("tts_models/en/ljspeech/tacotron2-DDC").to("cuda")
            else:
                self.tts_coqui = TTS("tts_models/en/ljspeech/tacotron2-DDC")
            self.engines['coqui'] = self.tts_coqui
            logger.info("Coqui TTS engine initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Coqui TTS: {e}")
    
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
        
        # OpenAI voices
        if 'openai' in self.engines:
            openai_voices = ['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer']
            for voice in openai_voices:
                voices.append(VoiceInfo(
                    engine="openai",
                    name=voice,
                    language="en",
                    gender="neutral"
                ))
        
        # Azure voices (sample)
        if 'azure' in self.engines:
            azure_voices = [
                ('en-US-AriaNeural', 'en', 'female'),
                ('en-US-DavisNeural', 'en', 'male'),
                ('en-US-JennyNeural', 'en', 'female'),
                ('en-US-GuyNeural', 'en', 'male'),
            ]
            for voice_name, lang, gender in azure_voices:
                voices.append(VoiceInfo(
                    engine="azure",
                    name=voice_name,
                    language=lang,
                    gender=gender
                ))
        
        return voices
    
    async def synthesize_speech(self, request: TTSRequest) -> TTSResponse:
        """Synthesize speech using the specified engine"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_filename = f"tts_{request.voice_engine}_{timestamp}.wav"
            audio_path = self.audio_dir / audio_filename
            
            if request.voice_engine == "pyttsx3":
                return await self._synthesize_pyttsx3(request, audio_path)
            elif request.voice_engine == "gtts":
                return await self._synthesize_gtts(request, audio_path)
            elif request.voice_engine == "openai":
                return await self._synthesize_openai(request, audio_path)
            elif request.voice_engine == "azure":
                return await self._synthesize_azure(request, audio_path)
            elif request.voice_engine == "coqui":
                return await self._synthesize_coqui(request, audio_path)
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
            
            # Get duration
            duration = self._get_audio_duration(audio_path)
            
            return TTSResponse(
                success=True,
                audio_file_path=str(audio_path),
                duration=duration,
                message="Speech synthesized successfully with pyttsx3"
            )
        except Exception as e:
            raise Exception(f"pyttsx3 synthesis failed: {e}")
    
    async def _synthesize_gtts(self, request: TTSRequest, audio_path: Path) -> TTSResponse:
        """Synthesize using Google Text-to-Speech"""
        try:
            tts = gTTS(text=request.text, lang=request.language or 'en', slow=False)
            tts.save(str(audio_path))
            
            duration = self._get_audio_duration(audio_path)
            
            return TTSResponse(
                success=True,
                audio_file_path=str(audio_path),
                duration=duration,
                message="Speech synthesized successfully with gTTS"
            )
        except Exception as e:
            raise Exception(f"gTTS synthesis failed: {e}")
    
    async def _synthesize_openai(self, request: TTSRequest, audio_path: Path) -> TTSResponse:
        """Synthesize using OpenAI TTS"""
        try:
            if 'openai' not in self.engines:
                raise Exception("OpenAI TTS not available - check API key")
            
            client = self.engines['openai']
            voice = request.voice_name or "alloy"
            
            response = client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=request.text
            )
            
            # Save audio
            with open(audio_path, "wb") as f:
                f.write(response.content)
            
            duration = self._get_audio_duration(audio_path)
            
            return TTSResponse(
                success=True,
                audio_file_path=str(audio_path),
                duration=duration,
                message="Speech synthesized successfully with OpenAI TTS"
            )
        except Exception as e:
            raise Exception(f"OpenAI TTS synthesis failed: {e}")
    
    async def _synthesize_azure(self, request: TTSRequest, audio_path: Path) -> TTSResponse:
        """Synthesize using Azure Speech Services"""
        try:
            if 'azure' not in self.engines:
                raise Exception("Azure Speech not available - check API credentials")
            
            speech_config = speechsdk.SpeechConfig(
                subscription=self.azure_speech_key,
                region=self.azure_speech_region
            )
            
            voice_name = request.voice_name or "en-US-AriaNeural"
            speech_config.speech_synthesis_voice_name = voice_name
            
            audio_config = speechsdk.audio.AudioOutputConfig(filename=str(audio_path))
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=speech_config,
                audio_config=audio_config
            )
            
            result = synthesizer.speak_text_async(request.text).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                duration = self._get_audio_duration(audio_path)
                return TTSResponse(
                    success=True,
                    audio_file_path=str(audio_path),
                    duration=duration,
                    message="Speech synthesized successfully with Azure Speech"
                )
            else:
                raise Exception(f"Azure synthesis failed: {result.reason}")
                
        except Exception as e:
            raise Exception(f"Azure Speech synthesis failed: {e}")
    
    async def _synthesize_coqui(self, request: TTSRequest, audio_path: Path) -> TTSResponse:
        """Synthesize using Coqui TTS"""
        try:
            if 'coqui' not in self.engines:
                raise Exception("Coqui TTS not available")
            
            tts = self.engines['coqui']
            tts.tts_to_file(text=request.text, file_path=str(audio_path))
            
            duration = self._get_audio_duration(audio_path)
            
            return TTSResponse(
                success=True,
                audio_file_path=str(audio_path),
                duration=duration,
                message="Speech synthesized successfully with Coqui TTS"
            )
        except Exception as e:
            raise Exception(f"Coqui TTS synthesis failed: {e}")
    
    def _get_audio_duration(self, audio_path: Path) -> float:
        """Get duration of audio file in seconds"""
        try:
            audio = AudioSegment.from_file(str(audio_path))
            return len(audio) / 1000.0  # Convert ms to seconds
        except Exception as e:
            logger.warning(f"Could not get audio duration: {e}")
            return 0.0
    
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

# Templates
templates = Jinja2Templates(directory="templates")

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
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .container { background: #f5f5f5; padding: 20px; border-radius: 10px; }
            textarea { width: 100%; height: 100px; margin: 10px 0; }
            select, input { margin: 5px; padding: 8px; }
            button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
            button:hover { background: #0056b3; }
            .audio-player { margin: 20px 0; }
            .voice-info { background: white; padding: 15px; margin: 10px 0; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎤 Modern Text-to-Speech System</h1>
            
            <form id="ttsForm">
                <div>
                    <label for="text">Text to convert:</label>
                    <textarea id="text" placeholder="Enter your text here..." required></textarea>
                </div>
                
                <div>
                    <label for="engine">TTS Engine:</label>
                    <select id="engine">
                        <option value="pyttsx3">pyttsx3 (Offline)</option>
                        <option value="gtts">Google TTS (Online)</option>
                        <option value="openai">OpenAI TTS (Premium)</option>
                        <option value="azure">Azure Speech (Premium)</option>
                        <option value="coqui">Coqui TTS (AI)</option>
                    </select>
                </div>
                
                <div>
                    <label for="voice">Voice:</label>
                    <select id="voice">
                        <option value="">Default</option>
                    </select>
                </div>
                
                <div>
                    <label for="rate">Speech Rate:</label>
                    <input type="range" id="rate" min="50" max="300" value="150">
                    <span id="rateValue">150</span>
                </div>
                
                <div>
                    <label for="volume">Volume:</label>
                    <input type="range" id="volume" min="0" max="1" step="0.1" value="1">
                    <span id="volumeValue">1.0</span>
                </div>
                
                <button type="submit">Generate Speech</button>
            </form>
            
            <div id="result" class="audio-player" style="display: none;">
                <h3>Generated Audio:</h3>
                <audio controls id="audioPlayer"></audio>
                <p id="status"></p>
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
                        document.getElementById('result').style.display = 'block';
                    } else {
                        document.getElementById('status').textContent = `Error: ${result.message}`;
                        document.getElementById('result').style.display = 'block';
                    }
                } catch (error) {
                    document.getElementById('status').textContent = `Error: ${error.message}`;
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
