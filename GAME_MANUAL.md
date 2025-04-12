# Train Station Game Manual

## Introduction
Welcome to the Train Station Adventure game! This is an interactive game where you navigate through a train station, interact with various NPCs, and complete objectives to board your train. The game features advanced AI-powered dialogue systems that support both text and voice input, as well as Japanese language support.

## Controls

### Movement
- **Arrow keys**: Move your character (up, down, left, right)
- **WASD keys**: Alternative movement controls (W=up, A=left, S=down, D=right)
- Movement is automatically normalized when moving diagonally

### Interacting with NPCs
When near an NPC, the game will show a prompt to interact. Each NPC has a specific key:
- **J key**: Talk to Hachiko (your dog companion)
- **E key**: Talk to Information Desk or Ticket Booth
- **E key**: Talk to Station Platform Attendant 1
- **R key**: Talk to Station Platform Attendant 2
- **T key**: Talk to Station Platform Attendant 3

## Dialogue System

### Text Input
- Type your message using the keyboard
- Press **Enter** to send your message
- Press **Backspace** to delete characters
- Press **Escape** to exit dialogue

### Voice Input
- Press **V key** or click the microphone button (🎤)
- Speak clearly into your microphone
- The system will automatically convert your speech to text
- The NPC will respond to your voice input with text and audio
- Voice input requires a working microphone and PyAudio

> **Note:** The Automatic Speech Recognition (ASR) functionality has not been fully tested across all platforms and environments. You may encounter occasional issues with voice detection or transcription accuracy. If you experience problems, please fall back to using text input.

### Text Navigation & Selection
- **Mouse wheel**: Scroll text up/down
- **Up/Down arrow keys**: Scroll one line
- **Page Up/Down keys**: Scroll an entire page
- **Click and drag**: Select text
- **Right-click** or **Ctrl+C**: Copy selected text to clipboard
- **Ctrl+V**: Paste clipboard text into input field

### Japanese Language Features
- NPC responses may contain both Japanese and English text
- Japanese text is displayed with a special header
- Text is automatically formatted for better readability

## Game Objectives

Your goal is to navigate the train station and complete the following objectives:

1. **Get Information**: Speak with the information booth attendant to learn about the train system
2. **Purchase a Ticket**: Find the ticket booth and buy a ticket
3. **Board the Train**: Find one of the three station platform attendants to check your ticket and board

Your current objective is displayed at the top of the screen.

## NPCs and Their Locations

### Hachiko (Dog Companion)
- Follows you around the station
- Provides helpful advice and conversation
- Talk to him by pressing the **J key** when nearby

### Information Attendant
- Located near the entrance of the station
- Provides information about trains and ticketing
- Talk to them by pressing the **E key** when nearby

### Ticket Booth Attendant
- Located at the ticket counter
- Sells train tickets
- Talk to them by pressing the **E key** when nearby

### Station Platform Attendants (1, 2, and 3)
- Located near the train platforms
- Check tickets and assist with boarding
- Each has a different interaction key (E, R, or T)

## Tips and Tricks

- The dog companion (Hachiko) provides helpful hints if you're stuck
- You can copy Japanese text by selecting it and using Ctrl+C or right-click
- Voice input is great for practicing Japanese conversation
- The game supports natural language understanding, so you can ask questions in different ways
- Looking for something specific? Try asking NPCs directly ("Where can I buy a ticket?")

## User Interface Elements

- **Text Output Box**: Shows NPC responses with both Japanese and English text when available
- **Input Box**: Where you type your responses
- **Voice Button**: Click to activate voice input
- **Scroll Indicators**: Arrows that appear when there's more text to scroll
- **Copy Feedback**: A message that appears briefly when text is copied
- **Current Objective**: Displayed at the top of the screen

## Troubleshooting

- **No audio from NPCs**: Check that your speakers are working and the AI TTS service is available
- **Voice input not working**: Ensure your microphone is connected and configured correctly
- **Japanese text not displaying**: The game requires a font that supports Japanese characters
- **Clipboard operations not working**: Make sure the pyperclip package is installed

## Credits

Train Station Adventure was created as an interactive language learning game featuring AI-powered NPCs that can understand and respond in both English and Japanese.

---

Enjoy your adventure at the train station! If you have any questions, try asking Hachiko or the Information Attendant within the game. 