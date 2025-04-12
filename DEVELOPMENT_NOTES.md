# Development Notes: Train Station Game

## Overview

This document captures key learnings from developing the Train Station Game, focusing on the technical challenges we faced and how we solved them. Integrating multiple AI services (speech recognition, NPC dialogue, text-to-speech) with a Pygame interface created some interesting problems that required creative solutions.

## Pygame and UI Challenges

### Text Rendering

Pygame's text rendering is primitive compared to modern web frameworks. Building a scrollable text box that could handle Japanese characters was surprisingly difficult:

- We had to implement word wrapping manually, since Pygame has no native support for it
- Japanese characters required special handling - they don't have convenient word boundaries
- We ended up rendering character-by-character for Japanese text to ensure proper wrapping

The final solution involved creating a custom `ScrollableTextBox` class that handles text rendering, scrolling, and selection. It's not perfect, but it works well enough for our purposes.

### Text Selection and Clipboard

Implementing text selection and clipboard functionality was a pain. Pygame doesn't have any built-in UI widgets for this, so we had to:

1. Track mouse events manually
2. Calculate text positions based on font metrics
3. Render selection highlights
4. Use the external `pyperclip` library to interface with the system clipboard

The biggest challenge was synchronizing the visual selection with the actual text data. Our first implementation tried to set attributes on Pygame surface objects, which failed miserably. We eventually switched to storing text content separately in tuples alongside the rendered surfaces.

### Audio Playback

Pygame's audio support is decent but not great for streaming audio from web services. We encountered:

- Format compatibility issues between the audio returned by the TTS service and what Pygame could play
- Playback timing problems, where text wouldn't display until after audio finished
- Initialization errors when trying to use Pygame's mixer simultaneously with PyAudio

We solved most of these by:
- Saving the audio to a temporary file before playing it
- Using threading to handle audio playback separately from UI updates
- Adding fallback methods when Pygame's mixer failed (like using system audio players)

## AI Service Integration

### ASR (Automatic Speech Recognition)

Recording and processing audio for speech recognition had several challenges:

- PyAudio availability issues across different platforms
- Background noise detection and handling
- Synchronous audio recording blocking the UI thread

Our solution involved:
- Making PyAudio optional with graceful fallbacks
- Threading the recording process
- Adding silence detection to automatically stop recording

### NPC AI Service

Working with the NPC dialogue service taught us a lot about handling API responses:

- Responses could be unpredictably structured
- Japanese text needed special markers for TTS processing
- Conversation history management became complex

We implemented:
- Robust error handling for service unavailability
- Session-based history tracking per NPC
- Special text markers to identify Japanese content

### TTS (Text-to-Speech)

The TTS service integration revealed challenges with:

- URL handling between services (relative vs. absolute URLs)
- Base64-encoded audio data vs. URL references
- Voice selection based on content language

We had to implement several fixes:
- URL completion for relative paths
- Multiple audio format support
- Language detection for appropriate voice selection

## Cross-Platform Gotchas

Some frustrating issues we encountered across platforms:

- Font availability for Japanese text rendering varied wildly
- Audio device initialization behaved differently on Windows, Mac, and Linux
- Clipboard operations had platform-specific quirks

Our solutions included:
- Downloading fonts if needed
- Multiple fallback methods for audio playback
- Platform detection and conditional code

## Threading Lessons

Working with threads in Pygame led to some important realizations:

- Pygame's event loop doesn't play nice with blocking operations
- UI updates need to happen on the main thread
- Audio recording and playback work better in separate threads

We implemented a pattern where:
1. UI responses happen immediately on the main thread
2. Audio processing runs in background threads
3. Thread communication is kept minimal and explicit

## What I'd Do Differently Next Time

If I were starting over:

1. Use a more modern UI framework with better text handling (maybe Arcade or PyQt)
2. Implement a proper event bus for communication between components
3. Design a better abstraction layer between services and game logic
4. Add proper caching for TTS responses to avoid redundant API calls
5. Create a more robust error recovery system for service outages

## Final Thoughts

Building this game was a great learning experience in integrating multiple AI services with an interactive UI. The biggest takeaway is that seemingly simple features (like displaying text!) can become complex when dealing with multiple languages, services, and platforms.

Despite the challenges, seeing users have natural conversations with AI NPCs in multiple languages made it all worthwhile. The text selection and copying features ended up being surprisingly useful for language learners who want to save phrases for later study.

Next time, I might explore using a web-based framework like React for the UI while keeping Python for the backend services - this would solve many of the text rendering and clipboard issues we faced, while still allowing us to use the AI services effectively. 