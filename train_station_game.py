import pygame
import sys
import math

# Initialize pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
PLAYER_SPEED = 5
DOG_SPEED = 4
INTERACTION_DISTANCE = 75
FONT_SIZE = 20
TEXT_INPUT_HEIGHT = 40
TEXT_OUTPUT_HEIGHT = 100
TEXT_COLOR = (255, 255, 255)
BG_COLOR = (0, 0, 0)
INPUT_BG_COLOR = (50, 50, 100)
OUTPUT_BG_COLOR = (100, 50, 50)

# Game states
STATE_EXPLORING = 0
STATE_DIALOGUE = 1

# Progression states
NEED_INFO = 0
NEED_TICKET = 1
NEED_CONDUCTOR = 2
GAME_COMPLETE = 3

# Setup the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Train Station Adventure")
clock = pygame.time.Clock()
font = pygame.font.Font(None, FONT_SIZE)

# Load background image and keep original size
background = pygame.image.load("assets/station-3-tracks.png")
MAP_WIDTH = background.get_width()
MAP_HEIGHT = background.get_height()

# Camera offset
camera_x = 0
camera_y = 0

def update_camera(player_x, player_y):
    # Calculate camera position to center on player
    camera_x = player_x - SCREEN_WIDTH // 2
    camera_y = player_y - SCREEN_HEIGHT // 2
    
    # Keep camera within map bounds
    camera_x = max(0, min(camera_x, MAP_WIDTH - SCREEN_WIDTH))
    camera_y = max(0, min(camera_y, MAP_HEIGHT - SCREEN_HEIGHT))
    
    return camera_x, camera_y

class Character:
    def __init__(self, x, y, image_path, name):
        self.x = x
        self.y = y
        self.width = 64
        self.height = 64
        self.name = name
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.image = pygame.image.load(image_path)
    
    def draw(self, screen, camera_x, camera_y):
        # Draw the character sprite with camera offset
        screen.blit(self.image, (self.x - camera_x, self.y - camera_y))
        
        # Debug visualization removed - only draw the character sprite
    
    def update_rect(self):
        self.rect.x = self.x
        self.rect.y = self.y

class Player(Character):
    def __init__(self, x, y, image_path):
        super().__init__(x, y, image_path, "Player")
        self.interacted_with_info = False
        self.interacted_with_ticket = False
        self.interacted_with_conductor = False
        self.progression_state = NEED_INFO
    
    def move(self, dx, dy, obstacles):
        # Store original position
        original_x = self.x
        original_y = self.y
        
        # Try moving on X axis first
        self.x += dx
        self.rect.x = self.x
        
        # Check X-axis collisions
        for obstacle in obstacles:
            if "Conductor" in obstacle.name:
                smaller_rect = pygame.Rect(
                    obstacle.rect.x + 40,
                    obstacle.rect.y + 40,
                    obstacle.rect.width - 80,
                    obstacle.rect.height - 80
                )
            else:
                smaller_rect = pygame.Rect(
                    obstacle.rect.x + 30,
                    obstacle.rect.y + 30,
                    obstacle.rect.width - 60,
                    obstacle.rect.height - 60
                )
            
            if self.rect.colliderect(smaller_rect):
                # Collision on X axis - move back
                if dx > 0:  # Moving right
                    self.x = smaller_rect.left - self.width
                elif dx < 0:  # Moving left
                    self.x = smaller_rect.right
                self.rect.x = self.x
        
        # Then try moving on Y axis
        self.y += dy
        self.rect.y = self.y
        
        # Check Y-axis collisions
        for obstacle in obstacles:
            if "Conductor" in obstacle.name:
                smaller_rect = pygame.Rect(
                    obstacle.rect.x + 40,
                    obstacle.rect.y + 40,
                    obstacle.rect.width - 80,
                    obstacle.rect.height - 80
                )
            else:
                smaller_rect = pygame.Rect(
                    obstacle.rect.x + 30,
                    obstacle.rect.y + 30,
                    obstacle.rect.width - 60,
                    obstacle.rect.height - 60
                )
            
            if self.rect.colliderect(smaller_rect):
                # Collision on Y axis - move back
                if dy > 0:  # Moving down
                    self.y = smaller_rect.top - self.height
                elif dy < 0:  # Moving up
                    self.y = smaller_rect.bottom
                self.rect.y = self.y
        
        # Keep player in map bounds
        self.x = max(0, min(MAP_WIDTH - self.width, self.x))
        self.y = max(0, min(MAP_HEIGHT - self.height, self.y))
        self.rect.x = self.x
        self.rect.y = self.y
        
        # If we're still colliding with something, revert to original position
        for obstacle in obstacles:
            if "Conductor" in obstacle.name:
                smaller_rect = pygame.Rect(
                    obstacle.rect.x + 40,
                    obstacle.rect.y + 40,
                    obstacle.rect.width - 80,
                    obstacle.rect.height - 80
                )
            else:
                smaller_rect = pygame.Rect(
                    obstacle.rect.x + 30,
                    obstacle.rect.y + 30,
                    obstacle.rect.width - 60,
                    obstacle.rect.height - 60
                )
            
            if self.rect.colliderect(smaller_rect):
                self.x = original_x
                self.y = original_y
                self.rect.x = self.x
                self.rect.y = self.y
                break
    
    def can_interact_with(self, npc, progression_state):
        # Check if player is close enough to interact
        distance = math.sqrt((self.x - npc.x)**2 + (self.y - npc.y)**2)
        
        # Different interaction distances based on NPC position
        if npc.name == "Ticket":
            max_distance = 100  # Keep ticket booth at 100
        elif "Conductor" in npc.name:
            max_distance = 75   # Increased from 50 to 75
        else:
            max_distance = INTERACTION_DISTANCE
            
        # Only check distance, no progression state requirements
        return distance <= max_distance

class Dog(Character):
    def __init__(self, x, y, image_path):
        super().__init__(x, y, image_path, "Dog")
        self.target_x = x
        self.target_y = y

    def talk(self, player_input=""):
        if player_input.lower() in self.dialogue:
            # If there's a specific response to this input
            return self.dialogue[player_input.lower()]
        elif self.dialogue_state < len(self.dialogue["default"]):
            # Return next default dialogue
            response = self.dialogue["default"][self.dialogue_state]
            self.dialogue_state += 1
            return response
        else:
            # Loop back to first response if we've gone through all dialogue
            self.dialogue_state = 0
            return self.dialogue["default"][0]

    def follow(self, target_x, target_y, obstacles):
        # Update target position
        self.target_x = target_x
        self.target_y = target_y
        
        # Calculate direction to player
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        distance = max(1, math.sqrt(dx*dx + dy*dy))  # Avoid division by zero
        
        # Normalize direction
        dx = dx / distance
        dy = dy / distance
        
        # Only move if far enough from player
        if distance > self.width:
            # Create a temporary rect for collision checking
            temp_rect = self.rect.copy()
            temp_rect.x += dx * DOG_SPEED
            temp_rect.y += dy * DOG_SPEED
            
            # Check for collisions
            collision = False
            for obstacle in obstacles:
                if temp_rect.colliderect(obstacle.rect) and obstacle != self:
                    collision = True
                    break
            
            # Update position if no collision
            if not collision:
                self.x += dx * DOG_SPEED
                self.y += dy * DOG_SPEED
                self.update_rect()

class NPC(Character):
    def __init__(self, x, y, image_path, name, dialogue):
        super().__init__(x, y, image_path, name)
        self.dialogue = dialogue
        self.dialogue_state = 0
        self.target_x = x
        self.target_y = y
    
    def talk(self, player_input=""):
        if player_input.lower() in self.dialogue:
            # If there's a specific response to this input
            return self.dialogue[player_input.lower()]
        elif self.dialogue_state < len(self.dialogue["default"]):
            # Return next default dialogue
            response = self.dialogue["default"][self.dialogue_state]
            self.dialogue_state += 1
            return response
        else:
            # Loop back to first response if we've gone through all dialogue
            self.dialogue_state = 0
            return self.dialogue["default"][0]
            
    def follow(self, target_x, target_y, obstacles):
        # Only the dog should follow
        if self.name != "Dog":
            return
            
        # Update target position
        self.target_x = target_x
        self.target_y = target_y
        
        # Calculate direction to player
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        distance = max(1, math.sqrt(dx*dx + dy*dy))  # Avoid division by zero
        
        # Normalize direction
        dx = dx / distance
        dy = dy / distance
        
        # Only move if far enough from player
        if distance > self.width:
            # Create a temporary rect for collision checking
            temp_rect = self.rect.copy()
            temp_rect.x += dx * DOG_SPEED
            temp_rect.y += dy * DOG_SPEED
            
            # Check for collisions
            collision = False
            for obstacle in obstacles:
                if temp_rect.colliderect(obstacle.rect) and obstacle != self:
                    collision = True
                    break
            
            # Update position if no collision
            if not collision:
                self.x += dx * DOG_SPEED
                self.y += dy * DOG_SPEED
                self.update_rect()

class DialogueSystem:
    def __init__(self):
        self.active = False
        self.current_npc = None
        self.input_text = ""
        self.output_text = ""
        self.input_rect = pygame.Rect(50, SCREEN_HEIGHT - TEXT_INPUT_HEIGHT - 20, SCREEN_WIDTH - 100, TEXT_INPUT_HEIGHT)
        self.output_rect = pygame.Rect(50, SCREEN_HEIGHT - TEXT_INPUT_HEIGHT - TEXT_OUTPUT_HEIGHT - 40, SCREEN_WIDTH - 100, TEXT_OUTPUT_HEIGHT)
    
    def activate(self, npc):
        self.active = True
        self.current_npc = npc
        self.input_text = ""
        self.output_text = npc.talk()  # Get initial dialogue
    
    def deactivate(self):
        self.active = False
        self.current_npc = None
    
    def handle_input(self, event, player):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                # Process input and get response
                response = self.current_npc.talk(self.input_text)
                self.output_text = response
                self.input_text = ""
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            elif event.key == pygame.K_ESCAPE:
                self.deactivate()
            else:
                self.input_text += event.unicode
    
    def draw(self, screen):
        if self.active:
            # Draw output box
            pygame.draw.rect(screen, OUTPUT_BG_COLOR, self.output_rect)
            pygame.draw.rect(screen, TEXT_COLOR, self.output_rect, 2)
            
            # Draw input box
            pygame.draw.rect(screen, INPUT_BG_COLOR, self.input_rect)
            pygame.draw.rect(screen, TEXT_COLOR, self.input_rect, 2)
            
            # Render NPC name
            npc_name_surface = font.render(f"{self.current_npc.name}:", True, TEXT_COLOR)
            screen.blit(npc_name_surface, (self.output_rect.x + 10, self.output_rect.y - 25))
            
            # Render output text (with word wrapping)
            words = self.output_text.split(' ')
            x, y = self.output_rect.x + 10, self.output_rect.y + 10
            line_spacing = font.get_linesize()
            for word in words:
                word_surface = font.render(word + ' ', True, TEXT_COLOR)
                word_width = word_surface.get_width()
                
                if x + word_width >= self.output_rect.right - 10:
                    x = self.output_rect.x + 10
                    y += line_spacing
                
                screen.blit(word_surface, (x, y))
                x += word_width
            
            # Render input text with cursor
            input_surface = font.render(self.input_text + '|', True, TEXT_COLOR)
            screen.blit(input_surface, (self.input_rect.x + 10, self.input_rect.y + 10))
            
            # Render instruction
            instruction = font.render("Press ENTER to send, ESC to exit dialogue", True, TEXT_COLOR)
            screen.blit(instruction, (self.input_rect.x, self.input_rect.y + self.input_rect.height + 5))

def main():
    # Set up dialogue
    dog_dialogue = {
        "default": [
            "Woof! I'm not an ordinary dog. I can talk!",
            "I think you should talk to the information booth first.",
            "I smell train conductors nearby! They're responsible for checking tickets.",
            "Trains are so exciting! I can't wait to go for a ride!"
        ],
        "hello": "Hey there! Nice to meet you!",
        "who are you": "I'm your loyal talking companion. Pretty special, right?",
        "help": "You need to speak with the information booth attendant first, then get a ticket, and finally talk to a conductor."
    }
    
    info_dialogue = {
        "default": [
            "Welcome to Central Station! How can I help you today?",
            "If you want to take a train, you'll need to purchase a ticket first.",
            "The ticket booth is just to your right.",
            "Let me know if you need any other information about the station."
        ],
        "hello": "Hello there! Welcome to Central Station.",
        "ticket": "You'll need to visit the ticket booth to buy a ticket.",
        "train": "Our trains run every 30 minutes. You'll need a ticket to board."
    }
    
    ticket_dialogue = {
        "default": [
            "Hello! Would you like to purchase a ticket?",
            "That will be $25. Here's your ticket.",
            "Please show your ticket to one of our conductors to board the train.",
            "Have a pleasant journey!"
        ],
        "yes": "Great! Here's your ticket for $25.",
        "how much": "A standard ticket costs $25.",
        "conductor": "There are three conductors on duty today. Any one of them can help you board."
    }
    
    conductor1_dialogue = {
        "default": [
            "Good day! May I see your ticket please?",
            "This ticket looks good. You're clear to board the train.",
            "The train will be departing shortly. Please take your seat.",
            "Enjoy your journey!"
        ],
        "ticket": "Yes, your ticket is valid. You may board the train.",
        "when": "The train departs in 10 minutes.",
        "where": "Your seat is in coach 3, seat 42B."
    }
    
    conductor2_dialogue = {
        "default": [
            "Hello there! Ticket, please.",
            "Thank you, your ticket is valid.",
            "The train is ready for boarding.",
            "Have a pleasant journey!"
        ],
        "time": "We're departing in 5 minutes sharp!",
        "help": "I'm happy to assist. What do you need?",
        "seat": "Your seat is in the third carriage."
    }
    
    conductor3_dialogue = {
        "default": [
            "Tickets, please! Can I see yours?",
            "All set! You're good to go.",
            "The train's about to leave. Better hurry!",
            "Safe travels!"
        ],
        "late": "Don't worry, we're running 2 minutes behind schedule.",
        "food": "There's a dining car in the middle of the train.",
        "bathroom": "Restrooms are available in every carriage."
    }
    
    # Create game objects - adjust positions based on map size
    player = Player(MAP_WIDTH // 2, MAP_HEIGHT // 2, "assets/player.png")  # Start player in center
    hachiko = NPC(MAP_WIDTH // 2 + 50, MAP_HEIGHT // 2, "assets/dog.png", "Hachiko", dog_dialogue)  # Dog follows player
    
    # Position NPCs according to the marked locations
    information_booth_attendant = NPC(MAP_WIDTH // 4, MAP_HEIGHT // 4, "assets/info_attendant.png", "Information", info_dialogue)
    ticket_booth_attendant = NPC(2 * MAP_WIDTH // 3, MAP_HEIGHT // 3, "assets/ticket_attendant.png", "Ticket", ticket_dialogue)
    
    # Position conductors - move 1 and 2 up towards track starts
    station_attendant_kyoto = NPC((MAP_WIDTH // 4) - 100, (2 * MAP_HEIGHT // 3) - 100, "assets/conductor1.png", "Conductor 1", conductor1_dialogue)  # Moved up
    station_attendant_odawara = NPC(3 * MAP_WIDTH // 4, (2 * MAP_HEIGHT // 3) - 100, "assets/conductor2.png", "Conductor 2", conductor2_dialogue)  # Moved up
    station_attendant_osaka = NPC((MAP_WIDTH // 2) - 100, (3 * MAP_HEIGHT // 4) - 20, "assets/conductor3.png", "Conductor 3", conductor3_dialogue)  # Keep in middle
    
    # Group NPCs
    npcs = [information_booth_attendant, ticket_booth_attendant, station_attendant_kyoto, station_attendant_odawara, station_attendant_osaka, hachiko]
    obstacles = [information_booth_attendant, ticket_booth_attendant, station_attendant_kyoto, station_attendant_odawara, station_attendant_osaka]  # Dog is not an obstacle
    
    # Setup dialogue system
    dialogue_system = DialogueSystem()
    
    # Game state
    game_state = STATE_EXPLORING
    camera_x = 0
    camera_y = 0
    
    # Main game loop
    running = True
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if game_state == STATE_EXPLORING:
                if event.type == pygame.KEYDOWN:
                    # Check for NPC interaction
                    for npc in npcs:
                        if player.can_interact_with(npc, player.progression_state):
                            # Different keys for different NPCs
                            if npc.name == "Hachiko" and event.key == pygame.K_d:
                                dialogue_system.activate(npc)
                                game_state = STATE_DIALOGUE
                                break
                            elif npc.name == "Conductor 1" and event.key == pygame.K_e:
                                dialogue_system.activate(npc)
                                game_state = STATE_DIALOGUE
                                break
                            elif npc.name == "Conductor 2" and event.key == pygame.K_r:
                                dialogue_system.activate(npc)
                                game_state = STATE_DIALOGUE
                                break
                            elif npc.name == "Conductor 3" and event.key == pygame.K_t:
                                dialogue_system.activate(npc)
                                game_state = STATE_DIALOGUE
                                break
                            elif (npc.name == "Information" or npc.name == "Ticket") and event.key == pygame.K_e:
                                dialogue_system.activate(npc)
                                game_state = STATE_DIALOGUE
                                break
            elif game_state == STATE_DIALOGUE:
                dialogue_system.handle_input(event, player)
                if not dialogue_system.active:
                    game_state = STATE_EXPLORING
        
        # Update game logic
        if game_state == STATE_EXPLORING:
            # Handle player movement
            keys = pygame.key.get_pressed()
            dx, dy = 0, 0
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:  # Support both arrow keys and WASD
                dx = -PLAYER_SPEED
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                dx = PLAYER_SPEED
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                dy = -PLAYER_SPEED
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                dy = PLAYER_SPEED
                
            # Normalize diagonal movement
            if dx != 0 and dy != 0:
                dx = dx * 0.707  # 1/√2
                dy = dy * 0.707  # 1/√2
            
            player.move(dx, dy, obstacles)
            
            # Dog follows player at a distance
            hachiko.follow(player.x + 50, player.y - 20, obstacles)  # Position dog to the right and slightly ahead
        
        # Update camera position
        camera_x, camera_y = update_camera(player.x, player.y)
        
        # Draw everything
        screen.fill(BG_COLOR)
        
        # Draw background with camera offset
        screen.blit(background, (-camera_x, -camera_y))
        
        # Draw characters with camera offset
        for npc in npcs:
            npc.draw(screen, camera_x, camera_y)
        player.draw(screen, camera_x, camera_y)
        
        # Draw interaction prompts with camera offset
        if game_state == STATE_EXPLORING:
            for npc in npcs:
                if player.can_interact_with(npc, player.progression_state):
                    if npc.name == "Hachiko":
                        key_text = "D"
                    elif npc.name == "Conductor 1":
                        key_text = "E"
                    elif npc.name == "Conductor 2":
                        key_text = "R"
                    elif npc.name == "Conductor 3":
                        key_text = "T"
                    else:
                        key_text = "E"
                    
                    prompt_text = font.render(f"Press {key_text} to talk to {npc.name}", True, TEXT_COLOR)
                    screen.blit(prompt_text, (npc.x - camera_x, npc.y - camera_y - 20))
        
        # Draw dialogue system if active (no camera offset needed for UI)
        if game_state == STATE_DIALOGUE:
            dialogue_system.draw(screen)
        
        # Draw progress indicator (no camera offset needed for UI)
        progress_text = ""
        if player.progression_state == NEED_INFO:
            progress_text = "Find information about taking a train"
        elif player.progression_state == NEED_TICKET:
            progress_text = "Purchase a ticket for the train"
        elif player.progression_state == NEED_CONDUCTOR:
            progress_text = "Find a conductor to board the train"
        elif player.progression_state == GAME_COMPLETE:
            progress_text = "Congratulations! You're ready to board the train!"
        
        progress_surface = font.render(progress_text, True, TEXT_COLOR)
        screen.blit(progress_surface, (10, 10))
        
        # Update display
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
