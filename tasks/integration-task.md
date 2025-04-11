# Task: Integrate Audio Dialogue System into Train Station Game

## Objective
Update the train_station_game.py file to incorporate the newly created audio_dialogue_system.py module, enabling voice-based interactions with NPCs alongside the existing text-based dialogue system.

## Requirements

1. Add the necessary imports for the AudioDialogueSystem class
2. Initialize the audio dialogue system in the main game initialization function
3. Create a new game state constant STATE_AUDIO_DIALOGUE to track audio interaction mode
4. Implement an alternative key input for triggering audio dialogue (use 'V' key for voice input)
5. Add event handling for audio recording start/stop and response playback
6. Implement UI indicators to show when the system is listening, processing, or responding
7. Create a helper function to process audio in a separate thread to prevent game freezing
8. Add visual feedback to display transcribed text and NPC responses during audio interactions
9. Ensure graceful fallback to text dialogue if audio interaction fails
10. Modify the existing DialogueSystem to use NPC-AI as the primary source of truth instead of the hardcoded dialogue dictionaries

## Implementation Notes
- The existing text dialogue system should remain fully functional but should be modified to use the NPC-AI system
- Keep the existing dialogue dictionaries (dog_dialogue, info_dialogue, etc.) only as fallback mechanisms, not as the primary source of dialogue responses
- Both text and audio interactions should use the NPC-AI system as the source of truth for dialogue
- The new audio dialogue system should work with all NPCs in the game
- Audio interactions should use the same game mechanics and progression as text interactions
- Use threading to handle audio processing to keep the game responsive

## File Paths
- Main game file: train_station_game.py
- Audio dialogue system: audio_dialogue_system.py

## Testing Guidelines
After implementation, test the game with both dialogue systems to ensure:
1. Both text and audio dialogues work for all NPCs
2. Game performance is maintained during audio processing
3. UI clearly indicates audio interaction status
4. Players can switch between text and audio modes seamlessly
