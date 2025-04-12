import requests
import json
import io
import time
import pygame
import threading
import numpy as np
from array import array
from pygame import mixer
import base64
import re
import os
import traceback
import uuid
import sys

# Debug mode for detailed logging
DEBUG_MODE = os.environ.get('AI_DEBUG', '0') == '1'

# Initialize pygame mixer for audio playback
try:
    pygame.mixer.quit()  # Reset mixer if already initialized
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
    debug_log = print if DEBUG_MODE else lambda *args, **kwargs: None
    print(f"Pygame mixer initialized: {pygame.mixer.get_init()}")
except Exception as e:
    print(f"Warning: Could not initialize pygame mixer: {e}")
    debug_log = print if DEBUG_MODE else lambda *args, **kwargs: None

# Make PyAudio optional
try:
    import pyaudio
    import wave
    PYAUDIO_AVAILABLE = True
except ImportError:
    print("Warning: PyAudio is not available. Voice input functionality will be disabled.")
    PYAUDIO_AVAILABLE = False

# Debug logging control - controlled by environment variable AI_DEBUG
DEBUG_LOGGING = DEBUG_MODE

# Function to handle debug logging
def debug_log(message):
    """Print debug messages only if DEBUG_LOGGING is enabled."""
    if DEBUG_LOGGING:
        print(f"[DEBUG] {message}")

# Function to detect Japanese text
def contains_japanese(text):
    # Check for Japanese characters
    japanese_pattern = re.compile(r'[\u3000-\u303f\u3040-\u309f\u30a0-\u30ff\uff00-\uff9f\u4e00-\u9faf]')
    return bool(japanese_pattern.search(text))

# Function to romanize Japanese text (simplified)
def romanize_japanese(text):
    """Very simple romanization for demo purposes."""
    # This is a very simplistic approach - in a real app, you'd use a proper library like pykakasi
    if not contains_japanese(text):
        return text
        
    # Simply format it as [JP_ORIGINAL:original_text:JP_ORIGINAL] with the original text only
    # No additional translation or romanization attempted
    return f"[JP_ORIGINAL:{text}:JP_ORIGINAL]"

# Check for environment variable to enable debug logging
try:
    if os.environ.get('AI_DEBUG') == '1':
        DEBUG_LOGGING = True
        print("Debug logging enabled")
except:
    pass

def debug_log(message):
    """Only print debug messages if DEBUG_LOGGING is enabled."""
    if DEBUG_LOGGING:
        print(message)

class AIServiceClient:
    """Client for interacting with ASR, NPC-AI, and TTS services."""
    
    # Class attribute for PyAudio availability
    PYAUDIO_AVAILABLE = PYAUDIO_AVAILABLE
    
    def __init__(self):
        # Service URLs
        self.asr_url = "http://localhost:8000"
        self.npc_ai_url = "http://localhost:8002"
        self.tts_url = "http://localhost:8001"
        
        # Service availability flags
        self.asr_available = False
        self.npc_ai_available = False
        self.tts_available = False
        
        # Check services on startup
        self.check_services()
        
        # Voice recording settings - only set if PyAudio is available
        if PYAUDIO_AVAILABLE:
            self.format = pyaudio.paInt16
            self.channels = 1
            self.rate = 16000
            self.chunk = 1024
            self.threshold = 500  # Audio threshold to detect voice
            self.silence_threshold = 30  # Frames of silence before stopping
        
        # Recording state
        self.is_recording = False
        self.recording_thread = None
        self.audio_data = None
        
        # NPC voice mapping
        self.npc_voices = {
            "Hachiko": "male1",
            "Information": "female1",
            "Ticket": "female2",
            "Station Platform Attendant 1": "male1",
            "Station Platform Attendant 2": "male2",
            "Station Platform Attendant 3": "male3"
        }
        
        # Conversation history
        self.conversation_history = {}
        
        # Initialize pygame mixer if not already initialized
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100)
    
    def check_services(self):
        """Check if the AI services are available."""
        try:
            # Check ASR service
            response = requests.get(f"{self.asr_url}/health", timeout=1)
            self.asr_available = response.status_code == 200
        except:
            self.asr_available = False
            
        try:
            # Check NPC-AI service - use the correct endpoint path
            response = requests.get(f"{self.npc_ai_url}/api/v1/health", timeout=1)
            self.npc_ai_available = response.status_code == 200
        except:
            self.npc_ai_available = False
            
        try:
            # Check TTS service
            response = requests.get(f"{self.tts_url}/health", timeout=1)
            self.tts_available = response.status_code == 200
        except:
            self.tts_available = False
            
        print(f"Services: ASR {'✓' if self.asr_available else '✗'}, NPC-AI {'✓' if self.npc_ai_available else '✗'}, TTS {'✓' if self.tts_available else '✗'}")
        return self.asr_available and self.npc_ai_available and self.tts_available
    
    def start_recording(self):
        """Start recording audio from microphone in a separate thread."""
        if not PYAUDIO_AVAILABLE:
            print("PyAudio is not available. Cannot record audio.")
            return False
            
        if self.is_recording:
            return False
            
        self.is_recording = True
        self.recording_thread = threading.Thread(target=self._record_audio)
        self.recording_thread.daemon = True
        self.recording_thread.start()
        return True
    
    def stop_recording(self):
        """Stop the ongoing recording and return the audio data."""
        if not PYAUDIO_AVAILABLE:
            return None
            
        if not self.is_recording:
            return None
            
        self.is_recording = False
        if self.recording_thread:
            self.recording_thread.join(timeout=1.0)
        
        return self.audio_data
    
    def _record_audio(self):
        """Record audio from microphone until silence is detected."""
        if not PYAUDIO_AVAILABLE:
            return
            
        p = pyaudio.PyAudio()
        stream = p.open(format=self.format, channels=self.channels,
                        rate=self.rate, input=True,
                        frames_per_buffer=self.chunk)
        
        print("Recording started...")
        
        frames = []
        silent_frames = 0
        
        while self.is_recording:
            data = stream.read(self.chunk)
            frames.append(data)
            
            # Check for silence
            audio_data = array('h', data)
            volume = max(abs(x) for x in audio_data)
            
            if volume < self.threshold:
                silent_frames += 1
                if silent_frames > self.silence_threshold:
                    break
            else:
                silent_frames = 0
        
        print("Recording stopped.")
        
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        # Save the recorded audio as WAV
        if frames:
            self.audio_data = self._save_to_wav(frames)
    
    def _save_to_wav(self, frames):
        """Convert raw audio frames to WAV format."""
        if not PYAUDIO_AVAILABLE:
            return None
            
        audio_data = io.BytesIO()
        wf = wave.open(audio_data, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(pyaudio.PyAudio().get_sample_size(self.format))
        wf.setframerate(self.rate)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        audio_data.seek(0)
        return audio_data
    
    def speech_to_text(self, audio_data):
        """Convert audio to text using ASR service."""
        if not self.asr_available:
            print("ASR service is not available")
            return ""
            
        try:
            files = {'audio': ('audio.wav', audio_data, 'audio/wav')}
            response = requests.post(f"{self.asr_url}/transcribe", files=files, timeout=5)
            response.raise_for_status()
            result = response.json()
            return result.get('text', '')
        except Exception as e:
            print(f"ASR service error: {e}")
            self.asr_available = False  # Mark as unavailable after an error
            return ""
    
    def get_npc_response(self, npc_name, player_text):
        """Get AI response from NPC-AI service."""
        if not self.npc_ai_available:
            print("NPC-AI service is not available")
            return None
            
        try:
            print(f"Getting response from NPC named: '{npc_name}'")
            
            # Map our NPC names to the NPC-AI service's expected IDs
            npc_id_mapping = {
                "Hachiko": "companion_dog",
                "Information": "information_booth_attendant",
                "Ticket": "ticket_booth_attendant",
                "Station Platform Attendant 1": "station_attendant_kyoto",
                "Station Platform Attendant 2": "station_attendant_odawara",
                "Station Platform Attendant 3": "station_attendant_osaka"
            }
            
            # Get the correct NPC ID for the service
            npc_id = npc_id_mapping.get(npc_name, npc_name)
            print(f"Mapped NPC '{npc_name}' to NPC-AI ID: '{npc_id}'")
            
            # Get or initialize conversation history for this NPC
            if npc_name not in self.conversation_history:
                print(f"Creating new conversation history for '{npc_name}'")
                self.conversation_history[npc_name] = []
            
            # Add player message to history (just for our local tracking)
            self.conversation_history[npc_name].append({"role": "user", "content": player_text})
            
            # Generate a session ID based on the NPC name
            session_id = f"{npc_id}_{hash(npc_name)}"[:20]
            
            # Prepare payload for NPC-AI service with correct field names according to docs
            payload = {
                "npc_id": npc_id,
                "player_id": "player1",
                "message": player_text,
                "session_id": session_id
            }
            
            # Log the full request JSON
            print(f"NPC-AI Request JSON: {json.dumps(payload, ensure_ascii=False, indent=2)}")
            
            print(f"Sending to NPC-AI for '{npc_name}' (ID: {npc_id}): {player_text}")
            response = requests.post(f"{self.npc_ai_url}/api/v1/chat", json=payload, timeout=10)
            
            if response.status_code != 200:
                print(f"NPC-AI service error: {response.status_code} {response.reason}")
                return None
            
            # Log the full response JSON
            print(f"NPC-AI Response JSON: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
            
            # Parse the response
            result = response.json()
            
            # Handle different response formats
            if 'response_text' in result:
                npc_response = result['response_text']
                print(f"Raw AI response: {npc_response}")
            elif 'response' in result:
                npc_response = result['response']
                print(f"Raw AI response: {npc_response}")
            elif 'message' in result:
                npc_response = result['message']
                print(f"Raw AI response: {npc_response}")
            elif 'reply' in result:
                npc_response = result['reply']
                print(f"Raw AI response: {npc_response}")
            elif 'text' in result:
                npc_response = result['text']
                print(f"Raw AI response: {npc_response}")
            elif isinstance(result, str):
                npc_response = result
                print(f"Raw AI response: {npc_response}")
            else:
                print(f"Unexpected response format")
                return None
            
            # Check if response is in Japanese and romanize if needed
            if contains_japanese(npc_response):
                print(f"Japanese response detected: {npc_response}")
                romanized = romanize_japanese(npc_response)
                npc_response = romanized
            
            # Add NPC response to history
            self.conversation_history[npc_name].append({"role": "assistant", "content": npc_response})
            
            return npc_response
        except Exception as e:
            print(f"NPC-AI service error: {e}")
            traceback.print_exc()
            self.npc_ai_available = False  # Mark as unavailable after an error
            return None
    
    def text_to_speech(self, text, speaker_name=""):
        """Convert text to speech using TTS service."""
        if not self.tts_available:
            print("TTS service is not available")
            return None
        
        debug_log(f"Converting to speech: {text[:50]}...")
        
        try:
            # Check if there's Japanese original text
            jp_original = None
            if "[JP_ORIGINAL:" in text and ":JP_ORIGINAL]" in text:
                start_idx = text.find("[JP_ORIGINAL:") + len("[JP_ORIGINAL:")
                end_idx = text.find(":JP_ORIGINAL]")
                if start_idx > 0 and end_idx > start_idx:
                    jp_original = text[start_idx:end_idx].strip()
                    debug_log(f"Found Japanese original text: {jp_original}")
            
            # Determine which voice to use based on the speaker
            voice = "female1"  # Default voice
            if speaker_name in self.npc_voices:
                voice = self.npc_voices[speaker_name]
                debug_log(f"Using voice {voice} for {speaker_name}")
            
            # Use Japanese voice for Japanese text if available
            if jp_original and contains_japanese(jp_original):
                voice = "japanese1"
                debug_log(f"Using Japanese voice for Japanese text")
                # For Japanese, use the original Japanese text
                tts_text = jp_original
            else:
                # For other languages, use the full text
                tts_text = text
            
            # Construct the payload
            payload = {
                "text": tts_text,
                "voice": voice,
                "language": "ja" if jp_original and contains_japanese(jp_original) else "en"
            }
            
            debug_log(f"TTS request: {json.dumps(payload)}")
            
            # Make the API request to the synthesis endpoint
            response = requests.post(
                f"{self.tts_url}/synthesize",
                json=payload,
                timeout=30  # Increased timeout for longer text
            )
            
            if response.status_code == 200:
                synthesis_result = response.json()
                debug_log("TTS response received")
                
                if "audio_content" in synthesis_result:
                    # The audio data is likely base64 encoded
                    audio_base64 = synthesis_result["audio_content"]
                    try:
                        # Decode base64 data to binary
                        audio_data = base64.b64decode(audio_base64)
                        debug_log(f"Decoded audio data length: {len(audio_data)} bytes")
                        return audio_data
                    except Exception as decode_error:
                        print(f"Failed to decode audio data: {decode_error}")
                        debug_log(f"Audio data: {audio_base64[:100]}...")
                        return None
                elif "audio_url" in synthesis_result:
                    # Audio is available at a URL
                    audio_url = synthesis_result["audio_url"]
                    debug_log(f"Audio URL from TTS service: {audio_url}")
                    
                    # Check if the URL is relative (no scheme) and add the base URL
                    if audio_url.startswith('/'):
                        # Get the base URL from self.tts_url
                        # Extract protocol and host from tts_url (e.g. http://localhost:8001)
                        tts_url_parts = self.tts_url.split('://')
                        if len(tts_url_parts) > 1:
                            scheme = tts_url_parts[0]
                            host = tts_url_parts[1].split('/')[0]
                            audio_url = f"{scheme}://{host}{audio_url}"
                            debug_log(f"Converted relative URL to absolute: {audio_url}")
                        else:
                            debug_log(f"Could not parse TTS URL: {self.tts_url}")
                            return None
                    
                    try:
                        debug_log(f"Fetching audio from URL: {audio_url}")
                        audio_response = requests.get(audio_url, timeout=10)
                        if audio_response.status_code == 200:
                            debug_log(f"Retrieved audio from URL: {len(audio_response.content)} bytes")
                            return audio_response.content
                        else:
                            print(f"Failed to retrieve audio: {audio_response.status_code}")
                            debug_log(f"Error response content: {audio_response.text[:100]}")
                            return None
                    except Exception as url_error:
                        print(f"Error retrieving audio from URL: {url_error}")
                        return None
                else:
                    print(f"Missing required fields in TTS response")
                    debug_log(f"TTS response: {synthesis_result}")
                    return None
            else:
                print(f"TTS service error: {response.status_code}")
                debug_log(f"Error response: {response.text}")
                return None
        except Exception as e:
            print(f"Error converting text to speech: {e}")
            traceback.print_exc()
            return None
    
    def play_audio(self, audio_data):
        """Play audio from data returned by TTS service."""
        if audio_data is None:
            debug_log("No audio data provided to play")
            return False
            
        debug_log(f"Attempting to play audio... Data type: {type(audio_data)}, Size: {len(audio_data) if isinstance(audio_data, bytes) else 'unknown'}")
        
        # Set a unique filename for temp files
        temp_id = str(uuid.uuid4())[:8]
        temp_file = f"temp_audio_{temp_id}.wav"
        
        try:
            # Convert to BytesIO if it's not already
            if isinstance(audio_data, bytes):
                debug_log("Converting bytes to BytesIO")
                audio_buffer = io.BytesIO(audio_data)
            else:
                audio_buffer = audio_data
                
            # Go back to the start of the buffer
            audio_buffer.seek(0)
            
            # First save to a temporary file - this approach is more reliable
            debug_log(f"Saving audio to temporary file: {temp_file}")
            with open(temp_file, "wb") as f:
                f.write(audio_buffer.read())
            
            # Try different playback methods
            playback_successful = False
            
            # Method 1: Play with pygame mixer
            try:
                debug_log("Attempting playback with pygame mixer")
                # Ensure mixer is initialized
                if not pygame.mixer.get_init():
                    debug_log("Initializing pygame mixer")
                    pygame.mixer.init(frequency=44100)
                
                # Load sound from file
                sound = pygame.mixer.Sound(temp_file)
                debug_log(f"Audio loaded, length: {sound.get_length():.2f} seconds")
                
                # Play the audio
                channel = sound.play()
                if channel:
                    debug_log("Sound playing on channel")
                    # Wait for it to finish
                    start_time = time.time()
                    max_wait = sound.get_length() + 2  # Add a 2-second buffer
                    
                    while channel.get_busy() and (time.time() - start_time) < max_wait:
                        pygame.time.wait(100)
                    
                    playback_successful = True
                    debug_log("Pygame audio playback completed")
            except Exception as e:
                debug_log(f"Pygame mixer playback failed: {e}")
                traceback.print_exc()
            
            # Method 2: System audio player (fallback)
            if not playback_successful:
                debug_log("Trying fallback audio playback")
                try:
                    if os.name == 'posix':  # macOS, Linux
                        # Check if we can use afplay (macOS) or aplay (Linux)
                        if os.system('which afplay > /dev/null 2>&1') == 0:
                            os.system(f'afplay "{temp_file}"')
                            debug_log("Used afplay for audio playback")
                            playback_successful = True
                        elif os.system('which aplay > /dev/null 2>&1') == 0:
                            os.system(f'aplay "{temp_file}"')
                            debug_log("Used aplay for audio playback")
                            playback_successful = True
                    elif os.name == 'nt':  # Windows
                        os.system(f'start /min wmplayer "{temp_file}"')
                        debug_log("Used Windows Media Player for audio playback")
                        playback_successful = True
                except Exception as e:
                    debug_log(f"System audio player failed: {e}")
            
            # Clean up
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    debug_log(f"Temporary file removed: {temp_file}")
            except Exception as e:
                debug_log(f"Failed to remove temporary file: {e}")
                
            return playback_successful
        except Exception as e:
            print(f"Error playing TTS audio: {e}")
            traceback.print_exc()
            
            # Try to clean up if possible
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass
                
            return False
    
    def process_voice_input(self, npc_name):
        """Process voice input through the entire pipeline.
        
        Returns a tuple: (text_response, audio_data)
        where text_response is the NPC's text response and audio_data is the audio to play.
        This allows the UI to display text immediately while audio is processed separately.
        """
        # Start recording
        if not self.start_recording():
            return None, None
            
        # Allow up to 5 seconds of recording
        for _ in range(50):  # 5 seconds at 0.1 second intervals
            pygame.time.wait(100)
            if not self.is_recording:
                break
                
        # Force stop if still recording
        audio_data = self.stop_recording()
        
        if not audio_data:
            return "I couldn't hear what you said.", None
            
        # Convert speech to text
        text = self.speech_to_text(audio_data)
        
        if not text:
            return "I couldn't hear what you said.", None
            
        # Get NPC response
        response = self.get_npc_response(npc_name, text)
        
        if not response:
            return "Sorry, I couldn't generate a response.", None
            
        # Convert response to speech
        audio = self.text_to_speech(response, npc_name)
        
        # Return both text and audio so the UI can handle them separately
        return response, audio 