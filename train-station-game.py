import pygame
import sys
import math
import os
import threading
import traceback
import pyperclip  # For clipboard operations
import urllib.request # For font download
import shutil # For font download

# Attempt to import custom AI services module
try:
    from ai_services import AIServiceClient  # Import our AI services
except ImportError:
    print("ERROR: Could not import 'ai_services'. Ensure 'ai_services.py' exists and provides AIServiceClient.")
    # Define a dummy class so the rest of the code doesn't immediately crash
    class AIServiceClient:
        def __init__(self):
            print("WARNING: Using dummy AIServiceClient. AI features will be disabled.")
            self.asr_available = False
            self.npc_ai_available = False
            self.tts_available = False
            self.PYAUDIO_AVAILABLE = False # Assume PyAudio might be needed

        def check_services(self):
            return False

        def get_npc_response(self, npc_name, text):
            print("Dummy AI: No response.")
            return None # Return None or a default scripted response

        def text_to_speech(self, text, npc_name):
            print("Dummy AI: No TTS.")
            return None

        def process_voice_input(self, npc_name):
             print("Dummy AI: No ASR.")
             return "Voice input unavailable (Dummy AI)", None

        def play_audio(self, audio_data):
             print("Dummy AI: Cannot play audio.")
             pass

        def stop_audio(self):
             print("Dummy AI: No audio to stop.")
             pass

        @property
        def is_playing_audio(self):
             return False


# Initialize pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
PLAYER_SPEED = 5
DOG_SPEED = 4  # Speed for Hachiko (NPC)
INTERACTION_DISTANCE = 75
FONT_SIZE = 20
TEXT_INPUT_HEIGHT = 80
TEXT_OUTPUT_HEIGHT = 250  # Increased from 160 to take up blocks 1 and 2
TEXT_COLOR = (255, 255, 255)
BG_COLOR = (0, 0, 0)
INPUT_BG_COLOR = (50, 50, 100)
OUTPUT_BG_COLOR = (100, 50, 50)
VOICE_ACTIVE_COLOR = (255, 0, 0)
VOICE_INACTIVE_COLOR = (100, 100, 100)
PROGRESS_BG_COLOR = (0, 0, 0, 180)  # Background color for progress text with alpha

# Game states
STATE_EXPLORING = 0
STATE_DIALOGUE = 1
# STATE_VOICE_INPUT is implicitly handled within STATE_DIALOGUE via dialogue_system.voice_active

# Progression states
NEED_INFO = 0
NEED_TICKET = 1
NEED_STATION_PLATFORM_ATTENDANT = 2
GAME_COMPLETE = 3

# Setup the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Train Station Adventure")
clock = pygame.time.Clock()

# --- Font Loading Logic ---
# Try to find/load a font that supports Japanese characters
# This section is complex due to the need for fallbacks if specific fonts aren't available.
try:
    # Expanded list of potential system fonts supporting Japanese
    available_fonts = pygame.font.get_fonts()
    japanese_fonts_to_try = [
        'msgothic', 'meiryo', 'hiragino kaku gothic pro', 'ms gothic', 'yu gothic',
        'yugothic', 'arialunicode', 'notosanscjkkr', 'notosanscjkjp', 'notosanscjktc', 'notosanscjkhk',
        'sourcehanhans', 'sourcehansans',
        # Generic CJK fonts sometimes included
        'stsong', 'simsun', 'nsimsun', 'malgungothic', 'microsoftyahei', 'microsoftjhenghei',
        'stxihei', 'fzshuti', 'fzyaoti'
    ]
    
    found_font_name = None
    for font_name in japanese_fonts_to_try:
        if font_name in available_fonts:
            try:
                # Test if the font can render a sample Japanese character
                test_font = pygame.font.SysFont(font_name, FONT_SIZE)
                test_font.render("あ", True, (0, 0, 0)) # Render a common Hiragana character
                font = test_font
                found_font_name = font_name
                print(f"Using system font with likely Japanese support: {found_font_name}")
                break
            except Exception as e:
                # Font exists but might not render Japanese properly or has other issues
                print(f"System font '{font_name}' found but failed test: {e}")
                continue
    
    if not found_font_name:
        print("No suitable pre-installed Japanese font found among common names. Attempting download...")
        # Create fonts directory if it doesn't exist
        os.makedirs("assets/fonts", exist_ok=True)
        
        # List of URLs to attempt downloading a Noto CJK font
        font_urls = [
            "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/Japanese/NotoSansJP-Regular.otf",
            "https://github.com/google/fonts/raw/main/ofl/notosansjp/NotoSansJP-Regular.ttf",
            # Add more fallbacks if needed
        ]
        
        font_downloaded_path = None
        for url in font_urls:
            try:
                filename = url.split('/')[-1]
                local_path = os.path.join("assets", "fonts", filename)
                
                # Download only if it doesn't exist
                if not os.path.exists(local_path):
                    print(f"Downloading font from {url}...")
                    with urllib.request.urlopen(url) as response, open(local_path, 'wb') as out_file:
                        shutil.copyfileobj(response, out_file)
                    print(f"Downloaded '{filename}'.")
                else:
                    print(f"Font '{filename}' already exists locally.")

                # Try loading the downloaded font
                font = pygame.font.Font(local_path, FONT_SIZE)
                # Test render again
                font.render("あ", True, (0, 0, 0))
                print(f"Successfully loaded font from: {local_path}")
                font_downloaded_path = local_path
                break # Stop after successful download and load

            except Exception as download_error:
                print(f"Failed to download or use font from {url}: {download_error}")
                if os.path.exists(local_path): # Clean up failed download attempt
                    try: os.remove(local_path)
                    except: pass
                continue
                
        if not font_downloaded_path:
             # Last resort - use pygame default font if download failed
            font = pygame.font.Font(None, FONT_SIZE)
            print("WARNING: Using pygame default font. Japanese characters may not display correctly.")

except Exception as e:
    # Catch-all for any unexpected error during font loading
    font = pygame.font.Font(None, FONT_SIZE)
    print(f"ERROR loading font: {e}. Using pygame default font. Japanese characters may not display correctly.")
    traceback.print_exc()

# Create a special render function that handles text rendering failures gracefully
def safe_render(text_to_render, target_font, color):
    """Attempts to render text, falling back to character-by-character or placeholders if errors occur."""
    try:
        # Try to render the whole text at once (most efficient)
        return target_font.render(text_to_render, True, color)
    except pygame.error as e:
        print(f"Warning: Pygame error rendering '{text_to_render[:20]}...': {e}. Trying character-by-character.")
    except Exception as e:
        print(f"Warning: Unexpected error rendering '{text_to_render[:20]}...': {e}. Trying character-by-character.")
        
    # If rendering the whole string fails, try character by character
    rendered_chars = []
    total_width = 0
    max_height = 0
    fallback_placeholder = "□" # Placeholder for unrenderable characters
    
    try:
        placeholder_surf = target_font.render(fallback_placeholder, True, color)
        placeholder_dims = placeholder_surf.get_size()
    except:
        # If even the placeholder fails, we're in trouble. Use a tiny surface.
        placeholder_surf = pygame.Surface((target_font.get_height() // 2, target_font.get_height()))
        placeholder_surf.fill((128, 128, 128)) # Gray square
        placeholder_dims = placeholder_surf.get_size()
        
    for char in text_to_render:
        try:
            char_surf = target_font.render(char, True, color)
            rendered_chars.append((char_surf, total_width))
            char_dims = char_surf.get_size()
            total_width += char_dims[0]
            max_height = max(max_height, char_dims[1])
        except:
            # If a character fails, use the placeholder
            rendered_chars.append((placeholder_surf, total_width))
            total_width += placeholder_dims[0]
            max_height = max(max_height, placeholder_dims[1])
            
    # If no characters could be rendered at all, return a small indicator surface
    if not rendered_chars:
        return pygame.Surface((10, target_font.get_linesize()), pygame.SRCALPHA)

    # Create a final surface to blit all the characters onto
    final_surface = pygame.Surface((total_width, max_height), pygame.SRCALPHA)
    final_surface.fill((0, 0, 0, 0))  # Transparent background
    
    for surf, x_pos in rendered_chars:
        final_surface.blit(surf, (x_pos, 0))
        
    return final_surface


# Load background image and get its original dimensions
try:
    background = pygame.image.load("assets/station-3-tracks.png").convert() # Use convert for performance
    MAP_WIDTH = background.get_width()
    MAP_HEIGHT = background.get_height()
except pygame.error as e:
    print(f"ERROR: Failed to load background image 'assets/station-3-tracks.png': {e}")
    # Create a fallback background
    MAP_WIDTH, MAP_HEIGHT = 1600, 1200 # Assume a large size if image fails
    background = pygame.Surface((MAP_WIDTH, MAP_HEIGHT))
    background.fill((30, 30, 30)) # Dark gray fallback
    error_text = safe_render("Background image not found!", font, (255, 0, 0))
    background.blit(error_text, (MAP_WIDTH // 2 - error_text.get_width() // 2, MAP_HEIGHT // 2 - error_text.get_height() // 2))


# Camera offset
camera_x = 0
camera_y = 0

def update_camera(player_x, player_y):
    """Calculates camera position to center on player, respecting map bounds."""
    target_camera_x = player_x - SCREEN_WIDTH // 2
    target_camera_y = player_y - SCREEN_HEIGHT // 2
    
    # Clamp camera to map boundaries
    cam_x = max(0, min(target_camera_x, MAP_WIDTH - SCREEN_WIDTH))
    cam_y = max(0, min(target_camera_y, MAP_HEIGHT - SCREEN_HEIGHT))
    
    return cam_x, cam_y

# --- Character Classes ---

class Character:
    """Base class for player and NPCs."""
    def __init__(self, x, y, image_path, name):
        self.x = x
        self.y = y
        self.width = 64  # Standard sprite size assumed
        self.height = 64
        self.name = name
        try:
            self.image = pygame.image.load(image_path).convert_alpha() # Use convert_alpha for transparency
        except pygame.error as e:
            print(f"ERROR: Failed to load image '{image_path}' for {name}: {e}")
            # Create a fallback colored square
            self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            fallback_color = (255, 0, 255) if name == "Player" else (0, 255, 0) # Magenta for player, Green for NPCs
            self.image.fill(fallback_color)
            pygame.draw.rect(self.image, (255,255,255), self.image.get_rect(), 1) # White border
        
        self.rect = pygame.Rect(x, y, self.width, self.height) # Main rect for position

    def draw(self, surface, cam_x, cam_y):
        """Draws the character sprite offset by the camera."""
        surface.blit(self.image, (self.x - cam_x, self.y - cam_y))
        
    def update_rect(self):
        """Updates the rect position based on x, y."""
        self.rect.topleft = (self.x, self.y)

class Player(Character):
    """Represents the player character."""
    def __init__(self, x, y, image_path):
        super().__init__(x, y, image_path, "Player")
        # Flags for tracking interaction progress (could be replaced by progression_state checks)
        self.interacted_with_info = False
        self.interacted_with_ticket = False
        self.interacted_with_station_platform_attendant = False
        self.progression_state = NEED_INFO # Start state
        
    def move(self, dx, dy, obstacles):
        """Moves the player and handles collisions with obstacles."""
        original_x = self.x
        original_y = self.y
        
        # --- Collision Detection ---
        # Move on X axis first
        self.x += dx
        self.update_rect()
        
        for obstacle in obstacles:
            # Use a slightly smaller collision box for NPCs to allow closer movement without 'sticking'
            # Especially important for narrower passages or when NPCs are close together.
            # Adjust the pixel values (e.g., 30, 60) if collision feels too tight or too loose.
            if "Station_Platform_Attendant" in obstacle.name: # Special case for attendants if needed
                obstacle_collision_rect = obstacle.rect.inflate(-80, -80) # Significantly smaller (40px inset)
            else:
                obstacle_collision_rect = obstacle.rect.inflate(-60, -60) # Standard smaller rect (30px inset)

            if self.rect.colliderect(obstacle_collision_rect):
                if dx > 0:  # Moving right
                    self.x = obstacle_collision_rect.left - self.width
                elif dx < 0:  # Moving left
                    self.x = obstacle_collision_rect.right
                self.update_rect() # Update rect after collision adjustment

        # Move on Y axis
        self.y += dy
        self.update_rect()

        for obstacle in obstacles:
            # Use the same smaller collision box logic for Y-axis check
            if "Station_Platform_Attendant" in obstacle.name:
                obstacle_collision_rect = obstacle.rect.inflate(-80, -80)
            else:
                 obstacle_collision_rect = obstacle.rect.inflate(-60, -60)

            if self.rect.colliderect(obstacle_collision_rect):
                if dy > 0:  # Moving down
                    self.y = obstacle_collision_rect.top - self.height
                elif dy < 0:  # Moving up
                    self.y = obstacle_collision_rect.bottom
                self.update_rect() # Update rect after collision adjustment

        # --- Boundary Checks ---
        # Keep player within map bounds
        self.x = max(0, min(MAP_WIDTH - self.width, self.x))
        self.y = max(0, min(MAP_HEIGHT - self.height, self.y))
        self.update_rect() # Final update after boundary checks
        
        # Final sanity check: If still colliding after adjustments (e.g., stuck in a corner), revert.
        # This can happen in tight spaces. Reverting prevents getting stuck inside obstacles.
        # for obstacle in obstacles:
        #     if "Station_Platform_Attendant" in obstacle.name:
        #          obstacle_collision_rect = obstacle.rect.inflate(-80, -80)
        #     else:
        #          obstacle_collision_rect = obstacle.rect.inflate(-60, -60)
        #     if self.rect.colliderect(obstacle_collision_rect):
        #         print(f"Warning: Stuck collision detected with {obstacle.name}. Reverting move.")
        #         self.x = original_x
        #         self.y = original_y
        #         self.update_rect()
        #         break # No need to check other obstacles if reverted

    def can_interact_with(self, npc, current_progression_state):
        """Checks if the player is close enough to interact with an NPC."""
        # Calculate distance between player center and NPC center for smoother interaction radius
        player_center_x = self.x + self.width / 2
        player_center_y = self.y + self.height / 2
        npc_center_x = npc.x + npc.width / 2
        npc_center_y = npc.y + npc.height / 2
        
        distance = math.sqrt((player_center_x - npc_center_x)**2 + (player_center_y - npc_center_y)**2)
        
        # Define interaction distances per NPC type (allows tuning)
        if npc.name == "Ticket":
            max_distance = 100 # Larger range for the ticket booth
        elif "Station_Platform_Attendant" in npc.name:
            max_distance = 75  # Standard interaction distance for attendants
        elif npc.name == "Hachiko":
             max_distance = 90 # Slightly larger for the dog, easier to talk to
        else: # Default for others like Information
            max_distance = INTERACTION_DISTANCE 
            
        # Interaction is purely based on distance now (progression checks happen elsewhere if needed)
        return distance <= max_distance


class NPC(Character):
    """Represents Non-Player Characters, including Hachiko."""
    def __init__(self, x, y, image_path, name, dialogue):
        super().__init__(x, y, image_path, name)
        self.dialogue = dialogue # Dictionary of dialogue options
        self.dialogue_state = 0 # Index for cycling through default dialogue
        self.target_x = x # Target position for movement (used by Hachiko)
        self.target_y = y

    def talk(self, player_input=""):
        """Returns a dialogue line based on player input or default progression."""
        player_input_lower = player_input.lower().strip() if player_input else ""

        if player_input_lower and player_input_lower in self.dialogue:
            # If there's a specific response mapped to this keyword
            response = self.dialogue[player_input_lower]
            # If the response itself is a list, cycle through it (less common setup)
            if isinstance(response, list):
                 # Simple cycling for keyword responses if they are lists
                 idx = self.dialogue.get(f"_{player_input_lower}_idx", 0)
                 line = response[idx % len(response)]
                 self.dialogue[f"_{player_input_lower}_idx"] = (idx + 1) % len(response)
                 return line
            else:
                 return response # Return the single string response
        elif "default" in self.dialogue and isinstance(self.dialogue["default"], list) and self.dialogue["default"]:
            # Cycle through the default dialogue list
            response = self.dialogue["default"][self.dialogue_state % len(self.dialogue["default"])]
            self.dialogue_state += 1
            return response
        elif "default" in self.dialogue:
             # If default is just a string
             return self.dialogue["default"]
        else:
            # Fallback if no dialogue is defined
            return f"{self.name}: ..." # Generic silent response

    def follow(self, target_x, target_y, obstacles):
        """Makes the NPC follow a target (specifically for Hachiko)."""
        # Only Hachiko should use the follow behavior
        if self.name != "Hachiko":
            return
            
        self.target_x = target_x
        self.target_y = target_y
        
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        # Stop following if very close to avoid jittering
        follow_distance_threshold = self.width * 1.5 # Start following when player is > 1.5 widths away
        stop_distance_threshold = self.width * 0.8 # Stop when closer than 0.8 widths

        if distance > follow_distance_threshold:
             move_speed = DOG_SPEED
        elif distance < stop_distance_threshold:
             return # Don't move if already close enough
        else:
             # Optional: Could slow down when getting closer
             move_speed = DOG_SPEED * (distance / follow_distance_threshold) # Slow down proportionally

        if distance > 1: # Avoid division by zero if already at target
            # Normalize direction vector
            norm_dx = dx / distance
            norm_dy = dy / distance
            
            # Calculate potential new position
            potential_x = self.x + norm_dx * move_speed
            potential_y = self.y + norm_dy * move_speed
            
            # --- Collision check for following NPC ---
            # Create a temporary rect for the potential new position
            temp_rect = self.rect.copy()
            temp_rect.topleft = (potential_x, potential_y)
            
            collision = False
            for obstacle in obstacles:
                # Use the obstacle's main rect for collision check with the following NPC
                if temp_rect.colliderect(obstacle.rect):
                    collision = True
                    # Optional: Add simple avoidance logic here? (e.g., try moving sideways)
                    # For now, just stop if collision is detected.
                    # print(f"{self.name} collision detected with {obstacle.name} while following.")
                    break
                    
            # Update position only if no collision
            if not collision:
                self.x = potential_x
                self.y = potential_y
                self.update_rect()

# --- UI Classes ---

class ScrollableTextBox:
    """Handles rendering, scrolling, and text selection/copying for dialogue output."""
    def __init__(self, rect, text_font, bg_color=(40, 40, 60, 230), text_color=(255, 255, 255), border_color=(150, 150, 200), border_width=2):
        self.rect = pygame.Rect(rect)
        self.font = text_font
        self.bg_color = bg_color
        self.text_color = text_color
        self.border_color = border_color
        self.border_width = border_width
        
        self.text = ""
        self.scroll_position = 0 # Index of the top visible line
        self.max_scroll = 0
        self.line_height = self.font.get_linesize()
        self.padding = 15 # Internal padding
        self.visible_lines = max(1, (self.rect.height - self.padding * 2) // self.line_height)
        
        self.rendered_lines = [] # List of tuples: (surface, original_text_string)
        self.line_positions = [] # Stores (y_pos, height) for each visible line, used for selection
        
        self.japanese_mode = False # Flag if Japanese text markers are detected
        
        # Text selection state
        self.selected_text = ""
        self.selection_active = False
        self.selection_start_line_idx = -1 # Index in self.rendered_lines
        self.selection_end_line_idx = -1   # Index in self.rendered_lines
        
        # Copy feedback timer
        self.copy_feedback_timer_end = 0 # Time when the "Copied!" message should disappear

        # Attempt to create slightly larger fonts for headers, fallback to main font
        try:
            # Use the same font file if possible, just larger size
            font_path = getattr(self.font, 'path', None) # Check if font object has path attribute
            if font_path:
                 self.header_font = pygame.font.Font(font_path, FONT_SIZE + 4)
                 self.japanese_font = pygame.font.Font(font_path, FONT_SIZE + 2) # Slightly larger for JP
            else: # If it's a SysFont or default font, try creating SysFont with larger size
                 font_name = getattr(self.font, 'name', "monospace") # Get name or default
                 self.header_font = pygame.font.SysFont(font_name, FONT_SIZE + 4)
                 self.japanese_font = pygame.font.SysFont(font_name, FONT_SIZE + 2)
        except Exception as e:
            print(f"Warning: Could not create larger fonts for headers/Japanese: {e}. Using default size.")
            self.header_font = self.font
            self.japanese_font = self.font # Fallback to the main font


    def set_text(self, new_text):
        """Sets the text content, performs wrapping, rendering, and scrolls to the end."""
        self.text = new_text if new_text else ""
        self.rendered_lines = []
        self.scroll_position = 0
        self.japanese_mode = False
        
        # Reset selection when text changes
        self.clear_selection()

        # Check for special Japanese text format: "[JP_ORIGINAL: <japanese_text> :JP_ORIGINAL] <translation>"
        jp_marker_start = "[JP_ORIGINAL:"
        jp_marker_end = ":JP_ORIGINAL]"
        
        if jp_marker_start in self.text and jp_marker_end in self.text:
            try:
                start_idx = self.text.find(jp_marker_start) + len(jp_marker_start)
                end_idx = self.text.find(jp_marker_end)
                
                if 0 <= start_idx < end_idx:
                    self.japanese_mode = True
                    japanese_text = self.text[start_idx:end_idx].strip()
                    translation_text = self.text[end_idx + len(jp_marker_end):].strip()
                    
                    # Add Japanese Header
                    header_surface = safe_render("Japanese:", self.header_font, (255, 255, 150)) # Yellowish
                    self.rendered_lines.append((header_surface, "Japanese:"))
                    # Add Japanese text, wrapped
                    self._render_wrapped_text(japanese_text, self.japanese_font, (255, 255, 200)) # Light Yellow
                    
                    # Add Separator (if both parts exist)
                    if japanese_text and translation_text:
                         separator = pygame.Surface((self.rect.width - self.padding * 2, 1))
                         separator.fill((180, 180, 180)) # Light gray line
                         self.rendered_lines.append((separator, "")) # Empty text for separator
                         # Add small spacing after separator
                         spacer = pygame.Surface((1, 5), pygame.SRCALPHA) # Transparent spacer
                         self.rendered_lines.append((spacer, ""))


                    # Add Translation Header (if translation exists)
                    if translation_text:
                         trans_header_surface = safe_render("Translation:", self.header_font, (200, 200, 255)) # Bluish
                         self.rendered_lines.append((trans_header_surface, "Translation:"))
                         # Add translated text, wrapped
                         self._render_wrapped_text(translation_text, self.font, self.text_color) # Normal font/color

                else: # Markers found but indices are wrong, treat as normal text
                    self._render_wrapped_text(self.text, self.font, self.text_color)
            except Exception as e: # Error during parsing/rendering Japanese format
                print(f"Error processing JP_ORIGINAL format: {e}. Displaying raw text.")
                traceback.print_exc()
                self.rendered_lines = [] # Clear partial rendering
                self._render_wrapped_text(self.text, self.font, self.text_color)
        else:
            # No special format, just render normally
            self._render_wrapped_text(self.text, self.font, self.text_color)
            
        # Calculate max scroll position based on rendered lines
        total_lines = len(self.rendered_lines)
        self.max_scroll = max(0, total_lines - self.visible_lines)
        
        # Always scroll to the end when new text is set
        self.scroll_to_end()

    def _render_wrapped_text(self, text_to_wrap, font_to_use, color):
        """Internal helper to wrap text and add rendered surfaces to self.rendered_lines."""
        max_width = self.rect.width - self.padding * 2 # Available width for text
        words = text_to_wrap.split(' ') # Simple space-based splitting
        
        current_line_str = ""
        for word in words:
            # Handle potential newlines within the text itself
            if '\n' in word:
                parts = word.split('\n')
                for i, part in enumerate(parts):
                    if not part: # Skip empty parts resulting from consecutive newlines
                         if current_line_str: # Render previous line before empty line
                             line_surface = safe_render(current_line_str, font_to_use, color)
                             self.rendered_lines.append((line_surface, current_line_str))
                         # Add an empty line explicitly to represent the newline
                         empty_surf = pygame.Surface((1, self.line_height // 2 )) # Minimal height surface for spacing
                         empty_surf.set_alpha(0) # Invisible
                         self.rendered_lines.append((empty_surf, ""))
                         current_line_str = "" # Start new line after newline
                         continue

                    test_line = current_line_str + (" " if current_line_str else "") + part
                    test_surface = safe_render(test_line, font_to_use, color)
                    
                    if test_surface.get_width() <= max_width:
                        current_line_str = test_line # Word fits, add to current line
                    else:
                        # Word doesn't fit, render the previous line
                        if current_line_str:
                            line_surface = safe_render(current_line_str, font_to_use, color)
                            self.rendered_lines.append((line_surface, current_line_str))
                        # Start new line with the current word/part
                        current_line_str = part
                        # Check if the single word/part itself is too long
                        word_surface = safe_render(current_line_str, font_to_use, color)
                        if word_surface.get_width() > max_width:
                             print(f"Warning: Word '{current_line_str[:20]}...' exceeds text box width. May look odd.")
                             # Render it anyway on its own line
                             self.rendered_lines.append((word_surface, current_line_str))
                             current_line_str = "" # Clear line as it was rendered

                    # Add the newline break logic within the loop
                    if i < len(parts) - 1: # If this wasn't the last part split by \n
                         if current_line_str: # Render the line before the explicit newline
                             line_surface = safe_render(current_line_str, font_to_use, color)
                             self.rendered_lines.append((line_surface, current_line_str))
                         # Add empty line for the newline char itself
                         empty_surf = pygame.Surface((1, self.line_height // 2 ))
                         empty_surf.set_alpha(0)
                         self.rendered_lines.append((empty_surf, ""))
                         current_line_str = "" # Reset for next line

            else: # Word does not contain newline
                test_line = current_line_str + (" " if current_line_str else "") + word
                test_surface = safe_render(test_line, font_to_use, color)

                if test_surface.get_width() <= max_width:
                    current_line_str = test_line # Word fits
                else:
                    # Word doesn't fit
                    if current_line_str: # Render previous line
                        line_surface = safe_render(current_line_str, font_to_use, color)
                        self.rendered_lines.append((line_surface, current_line_str))
                    current_line_str = word # Start new line with current word
                    # Check if the single word itself is too long
                    word_surface = safe_render(current_line_str, font_to_use, color)
                    if word_surface.get_width() > max_width:
                         print(f"Warning: Word '{current_line_str[:20]}...' exceeds text box width.")
                         self.rendered_lines.append((word_surface, current_line_str))
                         current_line_str = "" # Clear as it was rendered
        
        # Add the last remaining line
        if current_line_str:
            line_surface = safe_render(current_line_str, font_to_use, color)
            self.rendered_lines.append((line_surface, current_line_str))

    def handle_event(self, event):
        """Handles mouse wheel scrolling, clicks for selection, and keyboard shortcuts."""
        if not self.rect.collidepoint(pygame.mouse.get_pos()):
            # If mouse is outside the box, don't handle button events (except maybe global shortcuts)
             if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: # Left click outside clears selection
                  self.clear_selection()
                  return False # Event not handled *by the text box*
             elif event.type == pygame.KEYDOWN: # Handle global keys even if mouse is outside
                  if event.mod & pygame.KMOD_CTRL and event.key == pygame.K_c:
                       return self.copy_selected_text() # Try copying if text is selected
                  # Let other global keydowns (like ESC) be handled elsewhere
                  return False
             else:
                  return False # Ignore other events outside the box


        # --- Mouse Events Inside the Box ---
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:  # Scroll wheel up
                self.scroll_up()
                return True
            elif event.button == 5:  # Scroll wheel down
                self.scroll_down()
                return True
            elif event.button == 1:  # Left click - start selection
                self.start_selection(event.pos)
                return True
            elif event.button == 3: # Right click - copy selected text
                 return self.copy_selected_text()

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.selection_active:  # Left button up - end selection
                # We might not need end_selection if update_selection handles it continuously
                # self.end_selection(event.pos) # Let's rely on MOUSEMOTION update
                self.selection_active = False # Mark selection as finished
                return True

        elif event.type == pygame.MOUSEMOTION:
            if self.selection_active and event.buttons[0]:  # Left button held down and moving
                self.update_selection(event.pos)
                return True
                
        # --- Keyboard Events (Potentially global, but context matters) ---
        elif event.type == pygame.KEYDOWN:
            # Ctrl+C handled globally might be better, but check here too
            if event.mod & pygame.KMOD_CTRL and event.key == pygame.K_c:
                return self.copy_selected_text()

            # Scrolling keys
            elif event.key == pygame.K_PAGEUP:
                self.scroll_page_up()
                return True
            elif event.key == pygame.K_PAGEDOWN:
                self.scroll_page_down()
                return True
            elif event.key == pygame.K_UP:
                self.scroll_up()
                return True
            elif event.key == pygame.K_DOWN:
                self.scroll_down()
                return True
            elif event.key == pygame.K_HOME:
                 self.scroll_to_start()
                 return True
            elif event.key == pygame.K_END:
                 self.scroll_to_end()
                 return True

        return False # Event not handled by this text box

    def get_line_index_from_pos(self, pos):
        """Calculates the index in self.rendered_lines corresponding to a y-coordinate."""
        relative_y = pos[1] - self.rect.y - self.padding
        
        # Account for varying line heights if necessary (though usually constant)
        current_y = 0
        for idx, (line_y, line_h) in enumerate(self.line_positions):
             # line_y is absolute screen y, so adjust relative_y calculation or compare directly
             abs_y_in_box = pos[1] - self.rect.y
             
             # Check if the click y falls within the vertical bounds of this visible line
             # line_y is the top of the line on screen
             if line_y <= pos[1] < line_y + line_h:
                 return self.scroll_position + idx # Return the actual index in rendered_lines

        # If not found within the calculated positions (e.g., click below last line), guess based on average height
        estimated_line = int(relative_y / self.line_height)
        clamped_line = max(0, min(len(self.rendered_lines) - 1, self.scroll_position + estimated_line))
        return clamped_line

    def start_selection(self, pos):
        """Initiates text selection at the clicked line."""
        self.selection_active = True
        clicked_line_idx = self.get_line_index_from_pos(pos)
        self.selection_start_line_idx = clicked_line_idx
        self.selection_end_line_idx = clicked_line_idx
        self.update_selected_text() # Update internal selected text string

    def update_selection(self, pos):
        """Updates the end of the selection range as the mouse moves."""
        if not self.selection_active:
            return
        current_line_idx = self.get_line_index_from_pos(pos)
        self.selection_end_line_idx = current_line_idx
        self.update_selected_text()

    def update_selected_text(self):
        """Updates the `self.selected_text` string based on start/end line indices."""
        if self.selection_start_line_idx == -1 or self.selection_end_line_idx == -1:
            self.selected_text = ""
            return

        # Determine the actual start and end lines for selection range
        start = min(self.selection_start_line_idx, self.selection_end_line_idx)
        end = max(self.selection_start_line_idx, self.selection_end_line_idx)

        # Extract the text from the selected lines
        selected_lines_content = []
        for i in range(start, end + 1):
            if 0 <= i < len(self.rendered_lines):
                line_surf, line_text = self.rendered_lines[i]
                # Exclude separators/spacers/headers from copyable text
                if line_text and line_text not in ["Japanese:", "Translation:"]:
                    selected_lines_content.append(line_text)
        
        self.selected_text = "\n".join(selected_lines_content)
        # print(f"Selected range: {start}-{end}, Text: '{self.selected_text[:50]}...'") # Debug print

    def clear_selection(self):
         """Clears the current text selection."""
         self.selection_active = False
         self.selected_text = ""
         self.selection_start_line_idx = -1
         self.selection_end_line_idx = -1

    def copy_selected_text(self):
        """Copies the `self.selected_text` to the system clipboard."""
        if not self.selected_text:
            print("No text selected to copy.")
            return False # Indicate event not fully handled if nothing to copy

        try:
            pyperclip.copy(self.selected_text)
            print(f"Copied to clipboard: '{self.selected_text[:50]}...'")
            # Activate visual feedback
            self.copy_feedback_timer_end = pygame.time.get_ticks() + 1000 # Show for 1 second
            # Optionally clear selection after copy? User preference varies. Let's keep it selected.
            # self.clear_selection()
            return True # Indicate event was handled
        except Exception as e:
            print(f"ERROR: Failed to copy text to clipboard: {e}")
            traceback.print_exc()
            # Show error feedback? Maybe later.
            return False # Indicate event handling failed


    def scroll_up(self, lines=1):
        """Scrolls the text view up by a number of lines."""
        self.scroll_position = max(0, self.scroll_position - lines)

    def scroll_down(self, lines=1):
        """Scrolls the text view down by a number of lines."""
        self.scroll_position = min(self.max_scroll, self.scroll_position + lines)

    def scroll_page_up(self):
        """Scrolls up by the number of visible lines."""
        self.scroll_up(lines=self.visible_lines)

    def scroll_page_down(self):
        """Scrolls down by the number of visible lines."""
        self.scroll_down(lines=self.visible_lines)

    def scroll_to_start(self):
         """Scrolls to the very beginning of the text."""
         self.scroll_position = 0

    def scroll_to_end(self):
        """Scrolls to the very end of the text."""
        self.scroll_position = self.max_scroll
        
    def render(self, surface):
        """Renders the text box, its content, selection highlight, and scroll indicators."""
        # Draw background and border
        # Use SRCALPHA if bg_color has alpha, otherwise standard rect fill
        if len(self.bg_color) == 4:
             bg_surf = pygame.Surface(self.rect.size, pygame.SRCALPHA)
             bg_surf.fill(self.bg_color)
             surface.blit(bg_surf, self.rect.topleft)
        else:
             pygame.draw.rect(surface, self.bg_color, self.rect)
             
        pygame.draw.rect(surface, self.border_color, self.rect, self.border_width)
        
        # Define the clipping area for text rendering
        text_area_rect = self.rect.inflate(-self.padding * 2, -self.padding * 2)
        # surface.set_clip(text_area_rect) # Clipping can sometimes interfere with highlights, render carefully instead

        # Determine visible lines
        start_line_idx = self.scroll_position
        end_line_idx = min(start_line_idx + self.visible_lines, len(self.rendered_lines))
        
        # Determine selection range for highlighting
        selection_start = min(self.selection_start_line_idx, self.selection_end_line_idx)
        selection_end = max(self.selection_start_line_idx, self.selection_end_line_idx)
        has_selection = (selection_start != -1 and selection_end != -1)

        # Draw visible lines of text
        current_y = text_area_rect.y # Start drawing from the top padding edge
        self.line_positions = [] # Reset positions for this render pass

        for i in range(start_line_idx, end_line_idx):
            line_surface, line_text = self.rendered_lines[i]
            line_height = line_surface.get_height() if line_surface else self.line_height # Use actual height or default
             # Use a minimum line height for very short things like separators/spacers
            display_height = max(line_height, self.line_height // (2 if line_text else 1)) 

            # Check if this line is within the selection range
            is_selected = has_selection and (selection_start <= i <= selection_end)
            
            # Calculate line position relative to the main surface
            line_screen_y = self.rect.y + self.padding + (current_y - text_area_rect.y) # Convert back to screen coords
            self.line_positions.append((line_screen_y, display_height)) # Store screen Y and height


            # Draw selection highlight if needed
            if is_selected and line_text: # Only highlight lines with actual text content
                highlight_rect = pygame.Rect(
                    text_area_rect.x,
                    current_y,
                    text_area_rect.width, # Highlight full width
                    display_height
                )
                # Use a semi-transparent surface for the highlight
                highlight_surface = pygame.Surface(highlight_rect.size, pygame.SRCALPHA)
                highlight_surface.fill((100, 100, 255, 70))  # Semi-transparent blueish highlight
                surface.blit(highlight_surface, highlight_rect.topleft)

            # Blit the actual text/separator surface
            if line_surface:
                blit_pos = (text_area_rect.x, current_y)
                # Ensure rendering stays within the box vertically
                if current_y + display_height <= text_area_rect.bottom + 1 : # Allow blitting exactly at edge
                     surface.blit(line_surface, blit_pos)
            
            current_y += display_height # Move Y position down for the next line

        # surface.set_clip(None) # Remove clipping area

        # --- Draw UI Elements (Scroll indicators, Copy message) ---
        # Draw scroll indicators if necessary
        indicator_x = self.rect.right - self.padding / 2 # Position near the right edge
        if self.scroll_position > 0: # Up arrow
            pygame.draw.polygon(surface, self.text_color, [
                (indicator_x - 5, self.rect.y + 10), (indicator_x + 5, self.rect.y + 10), (indicator_x, self.rect.y + 5)
            ])
        if self.scroll_position < self.max_scroll: # Down arrow
             pygame.draw.polygon(surface, self.text_color, [
                (indicator_x - 5, self.rect.bottom - 10), (indicator_x + 5, self.rect.bottom - 10), (indicator_x, self.rect.bottom - 5)
            ])

        # Draw "Copied!" feedback message if active
        if pygame.time.get_ticks() < self.copy_feedback_timer_end:
            feedback_text = safe_render("Copied!", self.font, (100, 255, 100)) # Bright green
            feedback_rect = feedback_text.get_rect(center=(self.rect.centerx, self.rect.top + 25))
            # Add a small background to the feedback text
            feedback_bg = pygame.Surface((feedback_rect.width + 10, feedback_rect.height + 6), pygame.SRCALPHA)
            feedback_bg.fill((0, 0, 0, 180)) # Dark semi-transparent background
            feedback_bg.blit(feedback_text, (5, 3))
            surface.blit(feedback_bg, feedback_rect.inflate(10, 6).topleft) # Blit the background surface
            
        # Draw Copy Instruction Text (below the box) - Render once if possible
        instruction_text = "Click+drag or use Arrow/PgUp/Dn/Home/End to navigate. Right-click or Ctrl+C to copy selected."
        instruction_surf = safe_render(instruction_text, self.font, (200, 200, 180)) # Off-white color
        instruction_pos = (self.rect.x + self.padding, self.rect.bottom + 5)
        surface.blit(instruction_surf, instruction_pos)


class DialogueSystem:
    """Manages the dialogue UI, input handling, and interaction with AI services."""
    def __init__(self, text_font):
        self.active = False
        self.current_npc = None
        self.input_text = ""
        self.output_text = ""
        self.font = text_font # Use the globally loaded font

        # --- UI Layout ---
        # Output Box (Top 2/3rds roughly)
        self.output_rect = pygame.Rect(
            30,                              # Left padding
            50,                              # Top padding (below potential header)
            SCREEN_WIDTH - 60,               # Width (with padding)
            SCREEN_HEIGHT // 2 + 50          # Height (more than half)
        )
        
        # Input Box (Lower section)
        input_box_top = self.output_rect.bottom + 40 # Space below output box
        self.input_rect = pygame.Rect(
            30,                              # Left padding
            input_box_top,                   # Position below output
            SCREEN_WIDTH - 140,              # Width (leaving space for voice button)
            TEXT_INPUT_HEIGHT                # Height
        )
        
        # Voice Button (Right of input box)
        self.voice_button_rect = pygame.Rect(
            self.input_rect.right + 10,      # Position right of input box
            self.input_rect.y,               # Align top with input box
            60,                              # Width
            self.input_rect.height           # Height (match input box)
        )

        # Scrollable Text Box for Output
        self.text_box = ScrollableTextBox(
            self.output_rect, self.font,
            bg_color=OUTPUT_BG_COLOR + (230,), # Add alpha for slight transparency
            text_color=TEXT_COLOR,
            border_color=(180, 100, 100) # Darker red border
        )
        
        # AI Client and State
        self.ai_client = AIServiceClient() # Instantiate the (potentially dummy) client
        self.voice_active = False # Is currently listening?
        self.service_status_message = "" # Stores error messages like "ASR unavailable"
        self.check_ai_services() # Check status on init

        # Voice recording visual indicator state
        self.recording_indicator_alpha = 0
        self.recording_indicator_increasing = True


    def check_ai_services(self):
         """Checks AI service availability and sets status message."""
         self.service_status_message = "" # Clear previous status
         try:
             services_available = self.ai_client.check_services()
             
             # Create a more detailed status message
             status_parts = []
             if not hasattr(self.ai_client, 'asr_available') or not self.ai_client.asr_available:
                  status_parts.append("ASR unavailable")
             if not hasattr(self.ai_client, 'npc_ai_available') or not self.ai_client.npc_ai_available:
                  status_parts.append("NPC AI unavailable")
             if not hasattr(self.ai_client, 'tts_available') or not self.ai_client.tts_available:
                  status_parts.append("TTS unavailable")
             # Check for PyAudio specifically if needed by ai_client implementation
             if hasattr(self.ai_client, 'PYAUDIO_AVAILABLE') and not self.ai_client.PYAUDIO_AVAILABLE:
                  status_parts.append("PyAudio needed for mic")

             if status_parts:
                  self.service_status_message = "AI Status: " + ", ".join(status_parts)
             # else:
             #      self.service_status_message = "AI Services OK" # Optional success message

         except AttributeError as e:
              self.service_status_message = f"AI Status: Error checking services ({e}). Using fallbacks."
              # Ensure flags are set to false if check fails badly
              self.ai_client.asr_available = getattr(self.ai_client, 'asr_available', False)
              self.ai_client.npc_ai_available = getattr(self.ai_client, 'npc_ai_available', False)
              self.ai_client.tts_available = getattr(self.ai_client, 'tts_available', False)
              self.ai_client.PYAUDIO_AVAILABLE = getattr(self.ai_client, 'PYAUDIO_AVAILABLE', False)
         except Exception as e:
              self.service_status_message = f"AI Status: Unknown error checking services: {e}"
              print(f"ERROR checking AI services: {e}")
              traceback.print_exc()


    def activate(self, npc):
        """Activates the dialogue UI with a specific NPC."""
        if not npc:
             print("Error: Tried to activate dialogue with no NPC.")
             return
        self.active = True
        self.current_npc = npc
        self.input_text = ""
        self.voice_active = False # Ensure voice is off initially
        
        # Stop any currently playing audio from previous interactions
        try:
             if self.ai_client.is_playing_audio:
                 self.ai_client.stop_audio()
        except Exception as e:
             print(f"Error stopping previous audio: {e}")

        print(f"Activating dialogue with NPC: {npc.name}")
        
        # Display initial dialogue (scripted or potentially AI generated intro?)
        # For now, always use the NPC's predefined starting talk()
        self.output_text = npc.talk() # Get initial line
        self.text_box.set_text(self.output_text)
        
        # Check services again in case they became available/unavailable
        self.check_ai_services()

    def deactivate(self):
        """Deactivates the dialogue UI."""
        self.active = False
        self.current_npc = None
        self.voice_active = False
        # Stop any playing audio when dialogue closes
        try:
             if self.ai_client.is_playing_audio:
                 self.ai_client.stop_audio()
        except Exception as e:
             print(f"Error stopping audio on deactivate: {e}")
        print("Deactivating dialogue.")

    def handle_input(self, event):
        """Handles keyboard and mouse events relevant to the dialogue UI."""
        if not self.active:
            return # Do nothing if not active

        # 1. Let the scrollable text box handle its events first (scrolling, selection, copying)
        if self.text_box.handle_event(event):
            return # Event was handled by the text box

        # 2. Handle events specific to the dialogue system (input typing, sending, voice toggle, exit)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # If audio is playing, ESC stops audio first. Otherwise, it closes dialogue.
                try:
                    if self.ai_client.is_playing_audio:
                        print("Stopping audio playback via ESC.")
                        self.ai_client.stop_audio()
                    else:
                        self.deactivate()
                except Exception as e:
                     print(f"Error handling ESC key: {e}")
                     self.deactivate() # Ensure deactivation on error
                return True # ESC is handled

            elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                # Process the typed text input
                self.process_text_input()
                return True # Enter is handled

            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
                return True # Backspace is handled

            elif event.key == pygame.K_v: # 'V' key to toggle voice input
                 # Check if ASR is available *and* necessary components like PyAudio are ready
                 can_use_voice = getattr(self.ai_client, 'asr_available', False) and \
                                 getattr(self.ai_client, 'PYAUDIO_AVAILABLE', False) # Check PyAudio flag if needed
                 if can_use_voice:
                      self.toggle_voice_input()
                 else:
                      self.update_output("Voice input is not available.", is_error=True)
                 return True # 'V' key is handled

            # Handle Ctrl+V for pasting into input text
            elif event.mod & pygame.KMOD_CTRL and event.key == pygame.K_v:
                  try:
                       clipboard_text = pyperclip.paste()
                       if clipboard_text:
                            self.input_text += clipboard_text
                            print(f"Pasted text: {clipboard_text[:30]}...")
                  except Exception as e:
                       print(f"Failed to paste from clipboard: {e}")
                       traceback.print_exc()
                       self.update_output("Error pasting from clipboard.", is_error=True)
                  return True # Ctrl+V handled

            else:
                # Add typed character to input text
                self.input_text += event.unicode
                return True # Other keydown typing handled

        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Check if voice button was clicked
            if self.voice_button_rect.collidepoint(event.pos) and event.button == 1: # Left click
                 can_use_voice = getattr(self.ai_client, 'asr_available', False) and \
                                 getattr(self.ai_client, 'PYAUDIO_AVAILABLE', False)
                 if can_use_voice:
                      self.toggle_voice_input()
                 else:
                      self.update_output("Voice input is not available.", is_error=True)
                 return True # Voice button click handled
                 
            # Right-click already handled by text_box for copying if inside

        # Let other events pass through if not handled here
        return False

    def process_text_input(self):
        """Processes the text in the input box, gets response, updates output."""
        if not self.input_text.strip():
            return # Ignore empty input

        player_query = self.input_text
        self.input_text = "" # Clear input box immediately

        self.update_output(f"> You: {player_query}", is_user_input=True) # Show player input in log

        response_text = None
        audio_response = None

        # Try getting AI response first
        if getattr(self.ai_client, 'npc_ai_available', False):
            try:
                print(f"Sending to AI: NPC={self.current_npc.name}, Query='{player_query}'")
                response_text = self.ai_client.get_npc_response(self.current_npc.name, player_query)
                if response_text:
                     print(f"AI Response received: '{response_text[:60]}...'")
                     # Attempt TTS if available
                     if getattr(self.ai_client, 'tts_available', False):
                          try:
                               audio_response = self.ai_client.text_to_speech(response_text, self.current_npc.name)
                               if audio_response:
                                    print("TTS audio generated.")
                          except Exception as tts_err:
                               print(f"TTS Error: {tts_err}")
                               # Continue without audio if TTS fails
                else:
                     print("AI returned no response.")

            except Exception as ai_err:
                print(f"Error getting AI response: {ai_err}")
                traceback.print_exc()
                # Fall through to scripted dialogue on AI error

        # Fallback to scripted dialogue if AI is off or failed
        if response_text is None:
            print("Falling back to scripted dialogue.")
            response_text = self.current_npc.talk(player_query)

        # Update the output box and potentially play audio
        self.update_output(response_text) # Update UI first
        if audio_response:
             # Play audio in a separate thread to avoid blocking UI
             threading.Thread(target=self.safe_play_audio, args=(audio_response,), daemon=True).start()

    def toggle_voice_input(self):
        """Starts or stops voice input recording and processing."""
        if self.voice_active:
            print("Already recording voice.") # Or potentially stop recording? Decide behavior.
            # For now, pressing V again while recording does nothing. Click stops.
            return

        self.voice_active = True
        self.input_text = "" # Clear text input when starting voice
        print("Starting voice input...")
        self.update_output("Listening...", is_status=True) # Update UI to show listening

        # Run voice processing in a separate thread
        threading.Thread(target=self.run_voice_processing, daemon=True).start()


    def run_voice_processing(self):
        """Handles the actual voice recording, ASR, AI query, TTS, and playback."""
        response_text = None
        audio_response = None
        recognized_speech = None

        try:
            # This call should handle recording, ASR, sending to NPC AI, and getting TTS back
            # Modify AIServiceClient.process_voice_input if its signature/return differs
            # Expected return: (final_response_text, audio_bytes_or_path, recognized_speech_text)
            result = self.ai_client.process_voice_input(self.current_npc.name)

            if isinstance(result, tuple) and len(result) >= 2:
                 response_text, audio_response = result[:2]
                 if len(result) > 2:
                      recognized_speech = result[2] # Get the recognized text if returned
            else: # Handle older or different return signature
                 response_text = result # Assume it just returns text
                 audio_response = None # No audio returned

            if recognized_speech:
                 print(f"ASR Recognized: '{recognized_speech}'")
                 # Display recognized speech? Optional.
                 # self.update_output(f"> You (voice): {recognized_speech}", is_user_input=True)

            if response_text:
                print(f"AI Voice Response received: '{response_text[:60]}...'")
            else:
                response_text = "Sorry, I didn't get that." # Default if AI fails

        except Exception as e:
            print(f"Voice input processing error: {e}")
            traceback.print_exc()
            response_text = "There was an error processing your voice input."
            audio_response = None # Ensure no audio plays on error
        finally:
            self.voice_active = False # Mark voice as inactive regardless of outcome

        # Update UI and play audio (runs on the main thread via schedule or direct if safe)
        # Since this runs in a thread, directly updating Pygame UI elements might be unsafe.
        # A better approach is to queue the result for the main thread to process.
        # For simplicity here, we'll call update_output directly, but be aware of potential thread issues.
        
        # Show recognized text before the response
        if recognized_speech:
             self.update_output(f"> You (voice): {recognized_speech}", is_user_input=True)
             
        self.update_output(response_text) # Update text box
        if audio_response:
            self.safe_play_audio(audio_response) # Play the returned audio

    def update_output(self, text, is_error=False, is_user_input=False, is_status=False):
         """Adds text to the output box, handling potential formatting and scrolling."""
         if not text: return

         prefix = ""
         if is_error:
              prefix = "[ERROR] "
              # Maybe change text color temporarily? Complex with current setup.
         elif is_user_input:
              prefix = "" # Already formatted in calling function
         elif is_status:
               prefix = "[Status] "
         elif self.current_npc:
              prefix = f"{self.current_npc.name}: "

         full_text_line = f"{prefix}{text}"
         
         # Append to existing text in the box
         current_full_text = self.text_box.text
         new_full_text = current_full_text + "\n" + full_text_line if current_full_text else full_text_line
         
         self.text_box.set_text(new_full_text)
         # Setting text automatically scrolls to end

    def safe_play_audio(self, audio_data):
        """Plays audio using the AI client, with error handling."""
        if not audio_data: return
        try:
            self.ai_client.play_audio(audio_data)
        except Exception as e:
            print(f"Error playing audio: {e}")
            traceback.print_exc()
            # Maybe display an error in the text box?
            # self.update_output("Error playing audio response.", is_error=True)

    def draw(self, surface):
        """Draws the entire dialogue interface."""
        if not self.active:
            return

        # --- Draw Background Overlay ---
        # Solid black background for focus, or semi-transparent overlay
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 235)) # Dark, mostly opaque overlay
        surface.blit(overlay, (0, 0))

        # --- Draw UI Elements ---
        # 1. Output Text Box (using ScrollableTextBox)
        self.text_box.render(surface)

        # 2. Input Text Box Background and Border
        pygame.draw.rect(surface, INPUT_BG_COLOR, self.input_rect, border_radius=5)
        pygame.draw.rect(surface, (150, 150, 200), self.input_rect, 2, border_radius=5) # Border

        # 3. Input Text Rendering (with blinking cursor)
        cursor_char = '|' if pygame.time.get_ticks() % 1000 < 500 else ' '
        input_render_text = self.input_text + cursor_char
        input_surface = safe_render(input_render_text, self.font, TEXT_COLOR)
        # Position text inside the input box with padding
        input_text_pos = (self.input_rect.x + 10, self.input_rect.centery - input_surface.get_height() // 2)
        # Clip input text rendering if it exceeds the box width
        input_clip_rect = self.input_rect.inflate(-20, -10) # Area text can occupy
        surface.set_clip(input_clip_rect)
        # Adjust blit position if text is wider than the box (show the end)
        blit_x = input_text_pos[0]
        if input_surface.get_width() > input_clip_rect.width:
             blit_x = input_clip_rect.right - input_surface.get_width()

        surface.blit(input_surface, (blit_x, input_text_pos[1]))
        surface.set_clip(None) # Reset clipping


        # 4. Voice Input Button
        can_use_voice = getattr(self.ai_client, 'asr_available', False) and \
                        getattr(self.ai_client, 'PYAUDIO_AVAILABLE', False)
        voice_color = VOICE_ACTIVE_COLOR if self.voice_active else (
            VOICE_INACTIVE_COLOR if can_use_voice else (80, 80, 80) # Grayed out if unavailable
        )
        pygame.draw.rect(surface, voice_color, self.voice_button_rect, border_radius=5)
        pygame.draw.rect(surface, (200, 200, 220), self.voice_button_rect, 2, border_radius=5) # Border

        # Draw microphone icon inside the button
        try:
            # Mic icon - consider using an image if font emoji support is unreliable
            mic_icon_text = "🎤" # Microphone emoji
            mic_icon = safe_render(mic_icon_text, self.font, TEXT_COLOR if can_use_voice else (150, 150, 150))
            mic_rect = mic_icon.get_rect(center=self.voice_button_rect.center)
            surface.blit(mic_icon, mic_rect)
        except Exception as e:
             print(f"Warning: Could not render mic icon: {e}")
             fallback_mic = safe_render("MIC", self.font, TEXT_COLOR if can_use_voice else (150, 150, 150))
             mic_rect = fallback_mic.get_rect(center=self.voice_button_rect.center)
             surface.blit(fallback_mic, mic_rect)
             
        # 5. Instruction Text (below input box)
        instruction_y = self.input_rect.bottom + 10
        instruction_text = "Enter: Send | V/Click Mic: Speak | ESC: Exit"
        if self.voice_active:
             instruction_text = "Listening... (Press V or Click Mic to stop? - Check AI Service)" # Adjust based on stop behavior
        instruction_surf = safe_render(instruction_text, self.font, (200, 200, 200))
        instruction_pos = (self.input_rect.x, instruction_y)
        surface.blit(instruction_surf, instruction_pos)

        # 6. Service Status Text (below instructions)
        if self.service_status_message:
             status_color = (255, 100, 100) if "unavailable" in self.service_status_message.lower() or "error" in self.service_status_message.lower() else (150, 255, 150)
             status_surf = safe_render(self.service_status_message, self.font, status_color)
             status_pos = (instruction_pos[0], instruction_pos[1] + instruction_surf.get_height() + 5)
             surface.blit(status_surf, status_pos)

        # 7. Pulsing Recording Indicator (if voice active)
        if self.voice_active:
            # Update alpha for pulsing effect
            pulse_speed = 10
            if self.recording_indicator_increasing:
                self.recording_indicator_alpha += pulse_speed
                if self.recording_indicator_alpha >= 200:
                    self.recording_indicator_alpha = 200
                    self.recording_indicator_increasing = False
            else:
                self.recording_indicator_alpha -= pulse_speed
                if self.recording_indicator_alpha <= 50:
                    self.recording_indicator_alpha = 50
                    self.recording_indicator_increasing = True
            
            # Draw a subtle indicator bar at the top
            indicator_height = 5
            recording_surface = pygame.Surface((SCREEN_WIDTH, indicator_height), pygame.SRCALPHA)
            recording_surface.fill((255, 0, 0, self.recording_indicator_alpha)) # Pulsing red
            surface.blit(recording_surface, (0, 0))
            
            # Optionally, add "Recording..." text near the mic button
            rec_text = safe_render("Rec", self.font, (255, 255, 255))
            rec_pos = (self.voice_button_rect.centerx - rec_text.get_width()//2, self.voice_button_rect.bottom + 2)
            # surface.blit(rec_text, rec_pos) # Maybe too cluttered

# --- Main Game Logic ---

def main():
    """Main function to initialize and run the game."""
    global camera_x, camera_y # Allow main loop to update camera globals if needed (though return is cleaner)

    # --- Dialogue Content ---
    hachiko_dialogue = {
        "default": [
            "Woof! I'm Hachiko. I'm not an ordinary dog, you know. I can talk!",
            "Looks like you want to catch a train! You should probably talk to the information booth first.",
            "I smell... tickets! You'll need one of those. The ticket booth should be around here.",
            "Ah, the station platform attendants! They check the tickets. You'll need to show yours to one of them.",
            "Trains are so exciting! Where are you headed?"
        ],
        "hello": "Hey there! Nice day for a train journey!",
        "who are you": "I'm Hachiko! Your loyal talking companion for this station adventure.",
        "help": "Okay, listen up! First, talk to the Information attendant. Then, get a ticket from the Ticket booth. Finally, show your ticket to any Station Platform Attendant (Tanaka, Nakamura, or Yamada). Got it?",
        "treat": "Woof! Did someone say treat? I love treats!",
        "good boy": "Woof woof! *wags tail*"
    }
    
    info_dialogue = {
        "default": [
            "Welcome to Central Station! How can I assist you today?",
            "If you're looking to board a train, you'll need to purchase a ticket from the ticket booth.",
            "The ticket booth is located over there [Points generally right/up]. Mr. Sato should be able to help.",
            "Once you have your ticket, you'll need to present it to one of the station platform attendants near the tracks.",
            "Feel free to ask if you need directions or information about train schedules."
        ],
        "hello": "Hello! Welcome to Central Station. Need any information?",
        "ticket": "Yes, tickets can be purchased at the ticket booth. Just head over to Mr. Sato.",
        "train": "Trains depart regularly. Please check the schedule board or ask me for specific times. Remember to get your ticket first!",
        "where is": "Where is what specifically? The ticket booth? The platform? The restrooms?",
        "schedule": "The next train departs in 15 minutes from Platform 2. Other schedules are posted on the main board."
    }
    
    sato_dialogue = { # Ticket Attendant
        "default": [
            "Hello! Welcome to the ticket counter. Need a ticket for the train?",
            "One standard ticket coming right up. That will be $25, please.",
            "Thank you! Here is your ticket. Please keep it safe.",
            "You'll need to show this ticket to one of the station platform attendants - Mr. Tanaka, Mr. Nakamura, or Mr. Yamada - before boarding.",
            "Have a wonderful journey!"
        ],
        "yes": "Excellent! One ticket is $25. [Assumes payment] Here you go!",
        "how much": "A standard one-way ticket is $25.",
        "station platform attendant": "Yes, you can show your ticket to any of the three attendants near the platforms. They wear the blue uniforms.",
        "buy ticket": "Certainly. That's $25. [Assumes payment] Here's your ticket.",
        "no": "Alright. Let me know if you change your mind!"
    }
    
    tanaka_dialogue = { # Station Platform Attendant 1
        "default": [
            "Good day! Ready to board? May I see your ticket, please?",
            "[Checks ticket] Thank you. This looks perfectly in order.",
            "You're all set to board the train on Platform 1.",
            "Please mind the gap and find your seat quickly. We'll be departing soon!",
            "Enjoy your trip!"
        ],
        "ticket": "Ah, yes. Let me see... [Checks] Valid! You may board Platform 1.",
        "when": "The train is scheduled to depart in approximately 10 minutes.",
        "where": "This is Platform 1. Your carriage and seat number should be on your ticket.",
        "platform 1": "Yes, this is Platform 1. Right this way.",
        "hello": "Hello! Ticket please, if you're boarding."
    }
    
    nakamura_dialogue = { # Station Platform Attendant 2
        "default": [
            "Hello there! Ticket check. Could I see your ticket?",
            "[Examines ticket] Very good. Your ticket is valid for this train.",
            "You can board now via Platform 2.",
            "Watch your step getting on. The train will leave shortly.",
            "Have a safe and pleasant journey!"
        ],
        "ticket": "Let's have a look... [Checks] All good! Platform 2 is this way.",
        "time": "Departure is imminent! We're aiming to leave in about 5 minutes.",
        "help": "Certainly. Are you having trouble finding your platform or seat?",
        "platform 2": "Correct, this is Platform 2. Please board promptly.",
         "valid": "Yes, your ticket is valid. Proceed to Platform 2."
    }
    
    yamada_dialogue = { # Station Platform Attendant 3
        "default": [
            "Tickets, please! Show me your ticket if you're traveling today.",
            "[Glances at ticket] Alright, looks good!",
            "This way to Platform 3. Hurry now, boarding is almost complete!",
            "Find your seat and stow your luggage safely.",
            "Safe travels!"
        ],
        "ticket": "Ticket? [Checks] Yep, you're cleared for Platform 3.",
        "late": "We are running just a couple of minutes behind, but aiming to depart very soon!",
        "platform 3": "Yes, this is Platform 3. Please board now.",
        "food": "There is a dining car available on this train, usually located mid-train.",
        "bathroom": "Restrooms are available in most carriages. Look for the signs."
    }

    # --- Game Object Initialization ---
    try:
        player = Player(MAP_WIDTH // 2, MAP_HEIGHT // 2, "assets/player.png")
        # Instantiate Hachiko using the NPC class
        hachiko = NPC(MAP_WIDTH // 2 + 60, MAP_HEIGHT // 2 - 30, "assets/dog.png", "Hachiko", hachiko_dialogue)
        
        info_attendant = NPC(MAP_WIDTH // 4, MAP_HEIGHT // 4 + 50, "assets/info_attendant.png", "Information", info_dialogue)
        sato = NPC(2 * MAP_WIDTH // 3, MAP_HEIGHT // 3, "assets/ticket_attendant.png", "Ticket", sato_dialogue)
        
        # Station Platform Attendants near tracks
        track_y_level = (2 * MAP_HEIGHT // 3) - 150 # Position them higher up, nearer hypothetical track starts
        tanaka = NPC((MAP_WIDTH // 4) - 100, track_y_level, "assets/conductor1.png", "Station Platform Attendant 1", tanaka_dialogue)
        nakamura = NPC(3 * MAP_WIDTH // 4, track_y_level + 20, "assets/conductor2.png", "Station Platform Attendant 2", nakamura_dialogue) # Slightly lower Y
        yamada = NPC((MAP_WIDTH // 2), track_y_level - 20, "assets/conductor3.png", "Station Platform Attendant 3", yamada_dialogue) # Center, slightly higher Y
        
        # Lists for easy iteration
        all_characters = [player, hachiko, info_attendant, sato, tanaka, nakamura, yamada]
        npcs = [hachiko, info_attendant, sato, tanaka, nakamura, yamada] # NPCs only
        obstacles = [info_attendant, sato, tanaka, nakamura, yamada] # NPCs that block movement (Hachiko doesn't)
        
    except Exception as e:
        print(f"FATAL ERROR initializing game objects: {e}")
        traceback.print_exc()
        pygame.quit()
        sys.exit()

    # Setup dialogue system, passing the loaded font
    dialogue_system = DialogueSystem(font)
    
    # Game state
    game_state = STATE_EXPLORING
    camera_x, camera_y = update_camera(player.x, player.y) # Initial camera position

    # Progress text rendering optimization
    progress_surface = None
    progress_bg_surface = None
    last_progress_text = ""
    
    # --- Main Game Loop ---
    running = True
    while running:
        # --- Event Handling ---
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
                break # Exit event loop

            # Handle dialogue input first if active
            if game_state == STATE_DIALOGUE:
                dialogue_system.handle_input(event)
                # Check if dialogue was deactivated by input handler (e.g., ESC)
                if not dialogue_system.active:
                    game_state = STATE_EXPLORING
                    # Update progression state based on interaction *after* dialogue closes
                    last_npc_name = dialogue_system.current_npc.name if dialogue_system.current_npc else None # Get name before clearing
                    dialogue_system.current_npc = None # Clear NPC ref here just in case deactivate missed it
                    if last_npc_name == "Information" and player.progression_state == NEED_INFO:
                         player.progression_state = NEED_TICKET
                         player.interacted_with_info = True
                         print("Progression: Need Ticket")
                    elif last_npc_name == "Ticket" and player.progression_state == NEED_TICKET:
                         player.progression_state = NEED_STATION_PLATFORM_ATTENDANT
                         player.interacted_with_ticket = True
                         print("Progression: Need Station Platform Attendant")
                    elif "Station Platform Attendant" in (last_npc_name or "") and player.progression_state == NEED_STATION_PLATFORM_ATTENDANT:
                         player.progression_state = GAME_COMPLETE
                         player.interacted_with_station_platform_attendant = True
                         print("Progression: Game Complete!")
                continue # Skip exploration input if dialogue handled the event

            # Handle exploration input if dialogue is not active
            if game_state == STATE_EXPLORING:
                 if event.type == pygame.KEYDOWN:
                     interaction_triggered = False
                     # Check interaction keys (E, R, T for attendants, J for Hachiko)
                     for npc in npcs:
                         if player.can_interact_with(npc, player.progression_state):
                             key_to_press = None
                             if npc.name == "Hachiko": key_to_press = pygame.K_j
                             elif npc.name == "Station Platform Attendant 1": key_to_press = pygame.K_e
                             elif npc.name == "Station Platform Attendant 2": key_to_press = pygame.K_r
                             elif npc.name == "Station Platform Attendant 3": key_to_press = pygame.K_t
                             elif npc.name in ["Information", "Ticket"]: key_to_press = pygame.K_e # E for info/ticket

                             if event.key == key_to_press:
                                  # Check progression before allowing interaction
                                  can_talk = False
                                  if npc.name == "Information" and player.progression_state == NEED_INFO: can_talk = True
                                  elif npc.name == "Ticket" and player.progression_state == NEED_TICKET: can_talk = True
                                  elif "Station Platform Attendant" in npc.name and player.progression_state == NEED_STATION_PLATFORM_ATTENDANT: can_talk = True
                                  elif npc.name == "Hachiko": can_talk = True # Hachiko can always be talked to
                                  # Add else block for talking after game complete if desired

                                  if can_talk:
                                       print(f"Interaction key '{pygame.key.name(event.key)}' pressed for {npc.name}")
                                       dialogue_system.activate(npc)
                                       game_state = STATE_DIALOGUE
                                       interaction_triggered = True
                                       break # Stop checking other NPCs once interaction starts
                                  else:
                                       print(f"Cannot interact with {npc.name} yet (Progression State: {player.progression_state})")
                                       # Optional: Show a message like "You need to talk to X first"
                                       interaction_triggered = True # Prevent movement if key matches but interaction blocked
                                       break

                     # Prevent movement if an interaction key was pressed, even if blocked
                     # if interaction_triggered:
                     #      continue # Skip movement processing for this frame


        if not running: break # Exit loop if QUIT event occurred

        # --- Game Logic Update (only when exploring) ---
        if game_state == STATE_EXPLORING:
            # Player Movement Input
            keys = pygame.key.get_pressed()
            dx, dy = 0.0, 0.0 # Use float for diagonal normalization
            speed = PLAYER_SPEED
            
            if keys[pygame.K_LEFT] or keys[pygame.K_a]: dx -= speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += speed
            if keys[pygame.K_UP] or keys[pygame.K_w]: dy -= speed
            if keys[pygame.K_DOWN] or keys[pygame.K_s]: dy += speed
            
            # Normalize diagonal speed
            if dx != 0 and dy != 0:
                dx *= 0.7071 # Approx 1/sqrt(2)
                dy *= 0.7071
                
            # Move player if there was input
            if dx != 0 or dy != 0:
                player.move(dx, dy, obstacles)
            
            # Update Hachiko's following behavior
            # Position Hachiko slightly behind and to the side of the player
            target_follow_x = player.x - 30 if dx > 0 else (player.x + 30 if dx < 0 else player.x) # Trail behind direction
            target_follow_y = player.y + 40 # Always slightly below
            hachiko.follow(target_follow_x, target_follow_y, obstacles) # Hachiko follows player
            
            # Update camera based on player's new position
            camera_x, camera_y = update_camera(player.x, player.y)

        # --- Drawing ---
        # Clear screen or draw background
        screen.fill(BG_COLOR) # Fill with black as a base

        if game_state == STATE_EXPLORING:
             # Draw background image offset by camera
             screen.blit(background, (-camera_x, -camera_y))
             
             # Draw all characters (player and NPCs) offset by camera
             # Draw obstacles first, then non-obstacles, then player for layering?
             for npc in npcs: # Draw all NPCs
                 npc.draw(screen, camera_x, camera_y)
             player.draw(screen, camera_x, camera_y) # Draw player last (on top)

             # Draw interaction prompts near NPCs if close enough and progression allows
             for npc in npcs:
                 if player.can_interact_with(npc, player.progression_state):
                     key_char = '?'
                     can_talk_now = False
                     if npc.name == "Hachiko":
                          key_char = 'J'
                          can_talk_now = True # Always allowed
                     elif npc.name == "Station Platform Attendant 1":
                          key_char = 'E'
                          if player.progression_state == NEED_STATION_PLATFORM_ATTENDANT: can_talk_now = True
                     elif npc.name == "Station Platform Attendant 2":
                          key_char = 'R'
                          if player.progression_state == NEED_STATION_PLATFORM_ATTENDANT: can_talk_now = True
                     elif npc.name == "Station Platform Attendant 3":
                          key_char = 'T'
                          if player.progression_state == NEED_STATION_PLATFORM_ATTENDANT: can_talk_now = True
                     elif npc.name == "Information":
                          key_char = 'E'
                          if player.progression_state == NEED_INFO: can_talk_now = True
                     elif npc.name == "Ticket":
                          key_char = 'E'
                          if player.progression_state == NEED_TICKET: can_talk_now = True

                     if can_talk_now:
                          prompt_color = (255, 255, 0) if npc.name == "Hachiko" else TEXT_COLOR # Highlight dog prompt
                          prompt_text = f"Press [{key_char}] to talk"
                          prompt_surface = safe_render(prompt_text, font, prompt_color)
                          prompt_pos = (npc.x - camera_x + (npc.width // 2 - prompt_surface.get_width() // 2), npc.y - camera_y - 25)
                          
                          # Add a small background to the prompt for visibility
                          prompt_bg = pygame.Surface((prompt_surface.get_width() + 8, prompt_surface.get_height() + 4), pygame.SRCALPHA)
                          prompt_bg.fill((0, 0, 0, 160)) # Semi-transparent black background
                          prompt_bg.blit(prompt_surface, (4, 2))
                          screen.blit(prompt_bg, (prompt_pos[0]-4, prompt_pos[1]-2))
                     # Else: Optionally show grayed out prompt if interaction is possible but blocked by progression


             # Draw Progress Indicator (Top Left)
             current_progress_text = ""
             if player.progression_state == NEED_INFO: current_progress_text = "Objective: Talk to Information"
             elif player.progression_state == NEED_TICKET: current_progress_text = "Objective: Buy a Ticket"
             elif player.progression_state == NEED_STATION_PLATFORM_ATTENDANT: current_progress_text = "Objective: Show Ticket to Attendant"
             elif player.progression_state == GAME_COMPLETE: current_progress_text = "Objective: You can board the train!"
             
             if current_progress_text != last_progress_text: # Regenerate surface only if text changes
                 progress_surface = safe_render(current_progress_text, font, TEXT_COLOR)
                 last_progress_text = current_progress_text
                 if progress_surface:
                     padding = 8
                     progress_bg_surface = pygame.Surface(
                         (progress_surface.get_width() + padding*2, progress_surface.get_height() + padding*2),
                         pygame.SRCALPHA
                     )
                     progress_bg_surface.fill(PROGRESS_BG_COLOR)
                 else:
                      progress_bg_surface = None # Handle render failure

             # Draw the surfaces if they exist
             if progress_surface and progress_bg_surface:
                  screen.blit(progress_bg_surface, (10, 10)) # Position background
                  screen.blit(progress_surface, (10 + padding, 10 + padding)) # Position text over background

        elif game_state == STATE_DIALOGUE:
            # Draw dialogue system overlay and elements
            dialogue_system.draw(screen)

        # --- Update Display ---
        pygame.display.flip() # Update the full screen

        # --- Frame Rate Cap ---
        clock.tick(60) # Limit to 60 FPS

    # --- Cleanup ---
    print("Exiting game.")
    pygame.quit()
    sys.exit()


# --- Entry Point ---
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("\n--- UNEXPECTED ERROR ---")
        print(f"An error occurred during game execution: {e}")
        traceback.print_exc()
        print("------------------------")
        pygame.quit() # Attempt cleanup even on error
        sys.exit(1) # Indicate error exit status
