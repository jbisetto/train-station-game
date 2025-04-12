# Train Station Game

A simple Pygame-based interaction game where you play as a character with a talking dog, navigating through a train station and interacting with various NPCs to board a train. This game features AI-powered dialogues with Japanese language support.

This project was developed as the final immersion project for the [GenAI Cloud Project Bootcamp](https://genai.cloudprojectbootcamp.com/).

## Game Overview

In this game, you'll need to:
1. Talk to the information booth attendant
2. Purchase a ticket from the ticket booth
3. Get your ticket checked by one of three station platform attendants
4. You can also chat with your talking dog companion at any time!

## Installation & Setup

### Requirements
- Python 3.9 or higher
- Pygame library
- PyAudio (optional, for voice input)
- Pyperclip (for clipboard functionality)

### Installing Dependencies
```bash
pip install pygame pyaudio pyperclip
```

## Required AI Services

This game integrates with three external AI services that must be running for full functionality:

### 1. Automatic Speech Recognition (ASR)
- Repository: [https://github.com/jbisetto/whisper-api](https://github.com/jbisetto/whisper-api)
- Purpose: Converts player's voice input to text
- Default URL: http://localhost:8000

### 2. NPC AI Dialogue Service
- Repository: [https://github.com/jbisetto/npc-ai](https://github.com/jbisetto/npc-ai)
- Purpose: Generates NPC responses based on player input
- Default URL: http://localhost:8002

### 3. Text-to-Speech (TTS)
- Repository: [https://github.com/jbisetto/english-japanese-tts](https://github.com/jbisetto/english-japanese-tts)
- Purpose: Converts NPC text responses to spoken audio
- Default URL: http://localhost:8001

Please refer to the respective repositories for setup instructions. Each service can be run locally using Docker or directly with Python.


## Failed English-Japanese-Trancription AI Services
During the course of the work on this game another service was used for the ASR component. However; as much work that went into it and as promising as we had hoped it would be it was not able to transcribe our mixed language input requirements properly. We attach it here just to show the work that went into it. 

Thankfully, Whisper saved our butt on the day before submission. All hail open source.
- Repository: [https://github.com/jbisetto/english-japanese-transcriber](https://github.com/jbisetto/english-japanese-transcriber)

## Running the Game

Once you have the required dependencies and AI services running:

```bash
python train-station-game.py
```

## Game Controls

### Movement
- Arrow keys or WASD: Move your character
- E/J/R/T: Interact with NPCs when close enough (specific key depends on the NPC)

### In Dialogue
- Type to compose messages
- Enter: Send your message
- V: Toggle voice input mode
- Mouse wheel: Scroll through dialogue
- Click and drag: Select text
- Right-click or Ctrl+C: Copy selected text
- Ctrl+V: Paste text into input field
- Esc: Exit dialogue

## Documentation

For more detailed information about the game, please refer to:

- `GAME_MANUAL.md`: Comprehensive user guide with detailed instructions
- `DEVELOPMENT_NOTES.md`: Technical notes and insights about the implementation

## Game Features

- Top-down movement in a 2D environment
- AI-powered dialogue system with natural language processing
- Multilingual support with Japanese text and audio
- Voice input and speech recognition
- Text selection and clipboard integration
- Dog companion that follows you around
- Progressive gameplay with multiple NPCs

## Troubleshooting

If you encounter issues:

1. Ensure all three AI services are running correctly
2. Check that your microphone is properly configured for voice input
3. Verify that you have all required assets in the correct location
4. Make sure all Python dependencies are installed

## License

This project is provided as-is with no warranty. Feel free to modify and use for educational purposes.

Enjoy your train adventure!
