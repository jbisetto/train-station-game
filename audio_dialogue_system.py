import sys
sys.path.append("external/asr")
sys.path.append("external/npc-ai")
sys.path.append("external/tts")

# Import the components based on their actual module paths
from external.asr.src.agent import TranscriptionAgent  # ASR
from external.npc_ai.src.ai.npc import process_request, NPCRequest  # NPC-AI 
from external.tts.src.agent import TTSAgent  # TTS
from external.tts.src.config import Config  # For TTS

class ASRIntegration:
    def __init__(self):
        self.agent = TranscriptionAgent()
    
    def transcribe(self, audio_data):
        return self.agent.transcribe_audio(audio_data)

class NPCAIIntegration:
    def __init__(self):
        pass  # NPC-AI doesn't require initialization
    
    def process_input(self, text, npc_id):
        request = NPCRequest(
            request_id=npc_id,
            player_input=text
        )
        response = process_request(request)
        return response['response_text']

class TTSIntegration:
    def __init__(self):
        config = Config()  # TTS config
        self.agent = TTSAgent(config)
    
    def synthesize(self, text, output_path):
        return self.agent.synthesize(text, output_path)

class AudioDialogueSystem:
    def __init__(self):
        self.asr = ASRIntegration()
        self.npc_ai = NPCAIIntegration()
        self.tts = TTSIntegration()
        self.is_listening = False
        self.is_processing = False
        self.is_responding = False
    
    def start_recording(self):
        self.is_listening = True
        # Initialize recording here
        # This would be implemented with PyGame or another audio library
    
    def stop_recording(self, temp_file_path="temp_recording.wav"):
        self.is_listening = False
        # Stop recording and save to temp file
        return temp_file_path
    
    def process_audio_input(self, audio_path, npc_id):
        self.is_processing = True
        
        # ASR: Convert speech to text
        transcript = self.asr.transcribe(audio_path)
        
        # NPC-AI: Generate response
        response_text = self.npc_ai.process_input(transcript, npc_id)
        
        # TTS: Convert response to speech
        response_audio_path = "response_" + npc_id + ".wav"
        self.tts.synthesize(response_text, response_audio_path)
        
        self.is_processing = False
        self.is_responding = True
        
        return {
            "transcript": transcript,
            "response_text": response_text,
            "response_audio": response_audio_path
        }
    
    def play_response(self, audio_path):
        self.is_responding = True
        # Play audio response using PyGame
        # When done:
        self.is_responding = False