# Train Station Game

A simple Pygame-based interaction game where you play as a character navigating through a train station with Hachiko, your talking dog companion who serves as your Japanese language instructor and guide. You'll interact with various NPCs to board a train while practicing Japanese conversation. This game features AI-powered dialogues with Japanese language support.

This project was developed as the final immersion project for the [GenAI Cloud Project Bootcamp](https://genai.cloudprojectbootcamp.com/). I want to thank bootcamp organizer and instructor Andrew Brown at ExamPro for putting together the bootcamp.

## Game Overview

In this game, you'll need to:
1. Talk to the Information attendant at the information booth
2. Purchase a ticket from Sato at the ticket booth
3. Get your ticket checked by one of three platform attendants: Tanaka, Nakamura, or Yamada
4. Chat with Hachiko, your Japanese-speaking dog companion, who will provide guidance and language practice along the way!

## Installation & Setup

### Requirements
- Python 3.9 or higher
- Pygame library
- PyAudio (optional, for voice input)
- Pyperclip (for clipboard functionality)

### Installing Dependencies

We recommend using a virtual environment to avoid conflicts with other Python projects:

```bash
# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies from requirements.txt
pip install -r requirements.txt

# Additionally, ensure you have pyperclip for clipboard functionality
pip install pyperclip
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
- Hachiko, your loyal dog companion who serves as both a Japanese language instructor and guide
- Progressive gameplay with multiple NPCs in a simulated Japanese train station environment

## Troubleshooting

If you encounter issues:

1. Ensure all three AI services are running correctly
2. Check that your microphone is properly configured for voice input
3. Verify that you have all required assets in the correct location
4. Make sure all Python dependencies are installed

## License

This project is provided as-is with no warranty. Feel free to modify and use for educational purposes.

Enjoy your train adventure!

## NPCs and Characters

### Hachiko (Your Dog Companion)
- Named after the famous loyal Japanese Akita dog
- Acts as your personal Japanese language instructor
- Follows you around the station providing guidance
- Can translate phrases and explain Japanese customs
- Interact with Hachiko by pressing the **J key** when nearby

### Station Staff
- **Suzuki (Information Booth Attendant)**: Provides details about trains and station layout
- **Sato (Ticket Booth Attendant)**: Sells tickets and explains fare options
- **Platform Attendants**:
  - **Tanaka**: Station Platform Attendant 1 (E key)
  - **Nakamura**: Station Platform Attendant 2 (R key)
  - **Yamada**: Station Platform Attendant 3 (T key)

Each NPC speaks both English and Japanese, allowing you to practice your language skills in different contexts.
