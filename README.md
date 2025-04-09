**🚧🚧Note: This repository is currently under construction.🚧🚧**

# Train Station Interaction Game

A simple Pygame-based interaction game where you play as a character with a talking dog, navigating through a train station and interacting with various NPCs to board a train.

## Game Overview

In this game, you'll need to:
1. Talk to the information booth attendant
2. Purchase a ticket from the ticket booth
3. Get your ticket checked by one of three train conductors
4. You can also chat with your talking dog companion at any time!

## Installation & Setup

### Requirements
- Python 3.6 or higher
- Pygame library

### Installing Dependencies
```bash
pip install pygame
```

### Setting Up Assets
Place all PNG image files in an `assets` folder in the same directory as the game script:
- `player.png` - 64x64 image for the player character
- `dog.png` - 64x64 image for the dog
- `info_attendant.png` - 64x64 image for information booth attendant
- `ticket_attendant.png` - 64x64 image for ticket booth attendant  
- `conductor1.png` - 64x64 image for first train conductor
- `conductor2.png` - 64x64 image for second train conductor
- `conductor3.png` - 64x64 image for third train conductor

The directory structure should look like this:
```
train_station_game/
│
├── train_station_game.py
│
└── assets/
    ├── player.png
    ├── dog.png
    ├── info_attendant.png
    ├── ticket_attendant.png
    ├── conductor1.png
    ├── conductor2.png
    └── conductor3.png
```

## How to Play

1. Run the game:
```bash
python train_station_game.py
```

2. Controls:
   - Arrow keys: Move your character
   - E key: Interact with NPCs when close enough
   - In dialogue:
     - Type your responses
     - ENTER key: Send your message
     - ESC key: Exit dialogue

3. Gameplay:
   - Follow the objective shown at the top of the screen
   - Chat with NPCs in the required order to progress
   - You can have free-form conversations - try different questions!
   - Talk to your dog companion anytime for hints

## Game Features

- Top-down movement in a 2D environment
- Free-text dialogue input system
- Distinct input and output text boxes during conversations
- Dog companion that follows you around
- Clear progression system
- Multiple train conductors to choose from

## Extending the Game

Here are some ways you could enhance the game:
- Add more areas or a larger map
- Implement more complex dialogue branching
- Add train departure animations
- Include more NPCs with side quests
- Add sound effects and background music

## Troubleshooting

If you encounter any issues:
- Ensure all PNG files are in the correct directory
- Verify that Pygame is properly installed
- Check that all PNG files are 64x64 pixels

Enjoy your train adventure!
