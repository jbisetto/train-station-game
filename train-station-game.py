import pygame
import sys
import math
import os
from ai_services import AIServiceClient  # Import our AI services
import threading
import traceback
import pyperclip  # For clipboard operations

# Initialize pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
PLAYER_SPEED = 5
DOG_SPEED = 4
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
STATE_VOICE_INPUT = 2  # New state for voice input

# Progression states
NEED_INFO = 0
NEED_TICKET = 1
NEED_STATION_PLATFORM_ATTENDANT = 2
GAME_COMPLETE = 3

# Setup the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Train Station Adventure")
clock = pygame.time.Clock()

# Try to use a font that supports Japanese characters
try:
    # Expanded list of fonts that support Japanese
    available_fonts = pygame.font.get_fonts()
    japanese_fonts = [f for f in available_fonts if f in [
        'msgothic', 'meiryo', 'hiragino kaku gothic pro', 'ms gothic', 'yu gothic',
        'stsong', 'simsun', 'nsimsun', 'malgungothic', 'microsoftyahei', 'microsoftjhenghei',
        'yugothic', 'stxihei', 'fzshuti', 'fzyaoti'
    ]]
    
    if japanese_fonts:
        font = pygame.font.SysFont(japanese_fonts[0], FONT_SIZE)
        print(f"Using Japanese-compatible font: {japanese_fonts[0]}")
    else:
        # Try to download a font from multiple sources
        font_downloaded = False
        
        # Create fonts directory if it doesn't exist
        os.makedirs("assets/fonts", exist_ok=True)
        
        try:
            # First try to find any installed font that can render Japanese
            all_fonts = pygame.font.get_fonts()
            for test_font in all_fonts:
                try:
                    test = pygame.font.SysFont(test_font, FONT_SIZE)
                    # Test if the font can render Japanese
                    test.render("こんにちは", True, (0, 0, 0))
                    font = test
                    print(f"Found system font that supports Japanese: {test_font}")
                    font_downloaded = True
                    break
                except:
                    continue
        except Exception as e:
            print(f"Error finding system fonts: {e}")
            
        # If no system font worked, try downloading
        if not font_downloaded:
            urls = [
                "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/NotoSansCJKjp-Regular.otf",
                "https://github.com/googlefonts/noto-cjk/raw/main/Sans/Variable/OTF/NotoSansCJKjp-VF.otf",
                "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/Japanese/NotoSansJP-Regular.otf",
                "https://github.com/googlefonts/google-fonts/raw/main/ofl/notosansjp/NotoSansJP-Regular.ttf"
            ]
            
            for url in urls:
                try:
                    import urllib.request
                    import shutil
                    
                    filename = url.split('/')[-1]
                    local_path = f"assets/fonts/{filename}"
                    
                    print(f"Downloading Japanese font from {url}...")
                    urllib.request.urlretrieve(url, local_path)
                    
                    # Try to load the downloaded font
                    font = pygame.font.Font(local_path, FONT_SIZE)
                    # Test if it can render Japanese
                    font.render("こんにちは", True, (0, 0, 0))
                    print(f"Downloaded and loaded Japanese font successfully from {url}")
                    font_downloaded = True
                    break
                except Exception as download_error:
                    print(f"Failed to download or use font from {url}: {download_error}")
                    continue
            
        # If all download attempts failed, try to use a default monospace font
        if not font_downloaded:
            try:
                font = pygame.font.SysFont("monospace", FONT_SIZE)
                print("Using default monospace font - Japanese may not display correctly")
            except:
                # Last resort - use pygame default font
                font = pygame.font.Font(None, FONT_SIZE)
                print("Using pygame default font - Japanese may not display correctly")
except Exception as e:
    # If there's any error, use the default font
    font = pygame.font.Font(None, FONT_SIZE)
    print(f"Error loading font: {e}, using default")

# Create a special render function that handles Japanese text rendering failures gracefully
def safe_render(text, font, color):
    try:
        # Try to render the whole text
        return font.render(text, True, color)
    except:
        # If that fails, render character by character
        result_surfaces = []
        result_width = 0
        result_height = 0
        
        for char in text:
            try:
                char_surface = font.render(char, True, color)
                result_surfaces.append((char_surface, result_width))
                result_width += char_surface.get_width()
                result_height = max(result_height, char_surface.get_height())
            except:
                # If a character can't be rendered, use a placeholder
                try:
                    placeholder = font.render("□", True, color)
                    result_surfaces.append((placeholder, result_width))
                    result_width += placeholder.get_width()
                    result_height = max(result_height, placeholder.get_height())
                except:
                    # If even placeholder fails, skip this character
                    pass
        
        # Create a surface to hold all rendered characters
        if result_surfaces:
            result = pygame.Surface((result_width, result_height), pygame.SRCALPHA)
            result.fill((0, 0, 0, 0))  # Transparent background
            
            for surf, x_pos in result_surfaces:
                result.blit(surf, (x_pos, 0))
            
            return result
        else:
            # If nothing could be rendered, return an empty surface
            return pygame.Surface((10, font.get_linesize()), pygame.SRCALPHA)

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
        self.interacted_with_station_platform_attendant = False
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
            if "Station_Platform_Attendant" in obstacle.name:
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
            if "Station_Platform_Attendant" in obstacle.name:
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
            if "Station_Platform_Attendant" in obstacle.name:
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
        elif "Station_Platform_Attendant" in npc.name:
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
        if self.name != "Hachiko":
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

# New ScrollableTextBox class for better handling of text display
class ScrollableTextBox:
    def __init__(self, rect, font, bg_color=(40, 40, 60, 230), text_color=(255, 255, 255), border_color=(150, 150, 200), border_width=2):
        self.rect = rect
        self.font = font
        self.bg_color = bg_color
        self.text_color = text_color
        self.border_color = border_color
        self.border_width = border_width
        self.text = ""
        self.scroll_position = 0
        self.max_scroll = 0
        self.line_height = font.get_linesize()
        self.padding = 15
        self.visible_lines = (rect.height - self.padding * 2) // self.line_height
        self.rendered_lines = []
        self.japanese_mode = False
        self.render_success = True
        
        # Track selected text for copying
        self.selected_text = ""
        self.selection_active = False
        self.selection_start_pos = None
        self.selection_end_pos = None
        
        # Create larger fonts for headers and Japanese text
        try:
            self.header_font = pygame.font.Font(None, FONT_SIZE + 8)
            self.japanese_font = pygame.font.SysFont('arialunicode', FONT_SIZE + 4)
        except:
            self.header_font = self.font
            self.japanese_font = self.font
    
    def set_text(self, text):
        """Set text content and pre-render lines"""
        self.text = text
        self.rendered_lines = []
        self.scroll_position = 0
        self.render_success = True
        
        # Check for Japanese text
        if "[JP_ORIGINAL:" in text and ":JP_ORIGINAL]" in text:
            self.japanese_mode = True
            # Extract the original Japanese text
            start_idx = text.find("[JP_ORIGINAL:") + len("[JP_ORIGINAL:")
            end_idx = text.find(":JP_ORIGINAL]")
            if start_idx > 0 and end_idx > start_idx:
                japanese_text = text[start_idx:end_idx].strip()
                
                # Add separator line
                separator = pygame.Surface((self.rect.width - 20, 2))
                separator.fill((200, 200, 200))
                self.rendered_lines.append((separator, ""))
                
                # Add a header line with larger font
                header_surface = safe_render("Japanese Response:", self.header_font, (255, 200, 200))
                self.rendered_lines.append((header_surface, "Japanese Response:"))
                
                # Add some spacing
                spacing = pygame.Surface((5, 5))
                spacing.fill((0, 0, 0, 0))  # Transparent
                self.rendered_lines.append((spacing, ""))
                
                # Try to render Japanese text with larger Japanese font
                try:
                    jp_surface = safe_render(japanese_text, self.japanese_font, (255, 255, 150))
                    
                    # Check if we need to wrap the Japanese text based on width
                    if jp_surface.get_width() > self.rect.width - 20:
                        # Character by character approach for better wrapping
                        current_line = ""
                        current_width = 0
                        
                        for char in japanese_text:
                            char_surface = safe_render(char, self.japanese_font, (255, 255, 150))
                            char_width = char_surface.get_width()
                            
                            # If adding this character would overflow, render the current line
                            if current_width + char_width > self.rect.width - 40:  # More padding
                                if current_line:
                                    line_surface = safe_render(current_line, self.japanese_font, (255, 255, 150))
                                    self.rendered_lines.append((line_surface, current_line))
                                    current_line = char
                                    current_width = char_width
                                else:
                                    # If a single character is wider than the box, just add it anyway
                                    self.rendered_lines.append((char_surface, char))
                                    current_line = ""
                                    current_width = 0
                            else:
                                current_line += char
                                current_width += char_width
                        
                        # Add the last line if not empty
                        if current_line:
                            line_surface = safe_render(current_line, self.japanese_font, (255, 255, 150))
                            self.rendered_lines.append((line_surface, current_line))
                    else:
                        # If it fits, just add the whole surface
                        self.rendered_lines.append((jp_surface, japanese_text))
                except Exception as e:
                    # Fallback to normal font if Japanese font fails
                    print(f"Error rendering Japanese text with Japanese font: {e}")
                    jp_surface = safe_render(japanese_text, self.font, (255, 255, 150))
                    self.rendered_lines.append((jp_surface, japanese_text))
                
                # Add more spacing
                self.rendered_lines.append((spacing, ""))
                
                # Add another separator
                separator2 = pygame.Surface((self.rect.width - 20, 2))
                separator2.fill((200, 200, 200))
                self.rendered_lines.append((separator2, ""))
                self.rendered_lines.append((spacing, ""))
                
                # Add original text display
                rest_of_text = text[end_idx + len(":JP_ORIGINAL]"):].strip()
                if rest_of_text:
                    # Add translation header
                    trans_header = safe_render("Translation:", self.header_font, (200, 200, 255))
                    self.rendered_lines.append((trans_header, "Translation:"))
                    self.rendered_lines.append((spacing, ""))
                    
                    # Wrap translation text
                    self._render_wrapped_text(rest_of_text, self.text_color)
        else:
            self.japanese_mode = False
            # Regular text wrapping for non-Japanese text
            self._render_wrapped_text(text, self.text_color)
        
        # Calculate max scroll position
        total_lines = len(self.rendered_lines)
        self.max_scroll = max(0, total_lines - self.visible_lines)
        
        # Always scroll to end when new text is set
        self.scroll_to_end()
    
    def _render_wrapped_text(self, text, color):
        """Render text with word wrapping using safe_render"""
        words = text.split()
        current_line = ""
        for word in words:
            # Try with the current line plus this word
            test_line = current_line + " " + word if current_line else word
            test_surface = safe_render(test_line, self.font, color)
            
            if test_surface.get_width() > self.rect.width - 30:  # More padding
                # Line is too long, render current line and start a new one
                if current_line:
                    line_surface = safe_render(current_line, self.font, color)
                    # Store text in a dictionary to avoid attribute issues
                    self.rendered_lines.append((line_surface, current_line))
                current_line = word
            else:
                current_line = test_line
        
        # Add the last line if not empty
        if current_line:
            line_surface = safe_render(current_line, self.font, color)
            # Store text in a dictionary to avoid attribute issues
            self.rendered_lines.append((line_surface, current_line))
    
    def handle_event(self, event):
        """Handle mouse and keyboard events for scrolling and text selection"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                if event.button == 4:  # Mouse wheel up
                    self.scroll_up()
                    return True
                elif event.button == 5:  # Mouse wheel down
                    self.scroll_down()
                    return True
                elif event.button == 1:  # Left click to start selection
                    self.start_selection(event.pos)
                    return True
            elif event.button == 3:  # Right click anywhere = copy selected text
                if self.selected_text:
                    self.copy_selected_text()
                    return True
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.selection_active:  # Left button up = end selection
                self.end_selection(event.pos)
                return True
        
        elif event.type == pygame.MOUSEMOTION:
            if self.selection_active and pygame.mouse.get_pressed()[0]:  # Left button held
                self.update_selection(event.pos)
                return True
        
        elif event.type == pygame.KEYDOWN:
            # Keyboard shortcuts
            if event.mod & pygame.KMOD_CTRL:
                if event.key == pygame.K_c:  # Ctrl+C to copy
                    if self.selected_text:
                        self.copy_selected_text()
                        return True
            
            # Handle scrolling with keyboard
            if event.key == pygame.K_PAGEUP:
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
        
        return False
    
    def start_selection(self, pos):
        """Start text selection at the given position."""
        self.selection_active = True
        self.selection_start_pos = self.get_text_position_from_mouse(pos)
        self.selection_end_pos = self.selection_start_pos
        self.update_selected_text()
    
    def end_selection(self, pos):
        """End text selection at the given position."""
        self.selection_active = False
        self.selection_end_pos = self.get_text_position_from_mouse(pos)
        self.update_selected_text()
    
    def update_selection(self, pos):
        """Update the selection as the mouse moves."""
        self.selection_end_pos = self.get_text_position_from_mouse(pos)
        self.update_selected_text()
    
    def get_text_position_from_mouse(self, pos):
        """Convert mouse position to a position in the text."""
        # Calculate line based on y position
        relative_y = pos[1] - self.rect.y - self.padding
        line_index = int(relative_y / self.line_height) + self.scroll_position
        
        # Ensure line_index is valid
        if line_index < 0:
            line_index = 0
        elif line_index >= len(self.rendered_lines):
            line_index = max(0, len(self.rendered_lines) - 1)
            
        return (line_index, 0)  # Simplify by just selecting whole lines
    
    def update_selected_text(self):
        """Update the selected_text based on selection positions."""
        if not self.selection_start_pos or not self.selection_end_pos:
            self.selected_text = ""
            return
        
        # Ensure start position is before end position
        start_line, _ = self.selection_start_pos
        end_line, _ = self.selection_end_pos
        
        if start_line > end_line:
            start_line, end_line = end_line, start_line
        
        # Extract selected lines
        selected_lines = []
        for i in range(start_line, end_line + 1):
            if i < 0 or i >= len(self.rendered_lines):
                continue
            
            line_item = self.rendered_lines[i]
            if isinstance(line_item, tuple) and len(line_item) == 2:
                _, text = line_item
                if text and text.strip():  # Only add non-empty text
                    selected_lines.append(text)
        
        # Join the lines
        self.selected_text = "\n".join(selected_lines)
        print(f"Selected text: {self.selected_text[:50]}...")
    
    def copy_selected_text(self):
        """Copy selected text to clipboard."""
        if self.selected_text:
            try:
                print(f"Attempting to copy: {self.selected_text[:50]}...")
                pyperclip.copy(self.selected_text)
                print(f"Copied to clipboard: {self.selected_text[:50]}...")
                
                # Visual feedback for the copy operation
                self.copy_feedback_timer = pygame.time.get_ticks()
            except Exception as e:
                print(f"Failed to copy to clipboard: {e}")
                traceback.print_exc()
    
    def scroll_up(self):
        """Scroll up one line"""
        self.scroll_position = max(0, self.scroll_position - 1)
    
    def scroll_down(self):
        """Scroll down one line"""
        self.scroll_position = min(self.max_scroll, self.scroll_position + 1)
    
    def scroll_page_up(self):
        """Scroll up one page"""
        self.scroll_position = max(0, self.scroll_position - self.visible_lines)
    
    def scroll_page_down(self):
        """Scroll down one page"""
        self.scroll_position = min(self.max_scroll, self.scroll_position + self.visible_lines)
    
    def scroll_to_end(self):
        """Scroll to the end of the text"""
        self.scroll_position = self.max_scroll
    
    def render(self, surface):
        """Render the text box and its content"""
        # Draw background and border
        pygame.draw.rect(surface, self.bg_color, self.rect)
        pygame.draw.rect(surface, self.border_color, self.rect, self.border_width)
        
        # Calculate visible range
        start_line = self.scroll_position
        end_line = min(start_line + self.visible_lines, len(self.rendered_lines))
        
        # Draw visible lines
        y = self.rect.y + 15  # More top padding
        
        # Track the positions of each line for selection highlighting
        self.line_positions = []
        
        for i in range(start_line, end_line):
            item = self.rendered_lines[i]
            line_height = self.line_height
            line_y = y
            
            if isinstance(item, tuple) and len(item) == 2:
                # Unpack the tuple (surface, text)
                surface_item, text = item
                
                # Highlight selected lines
                is_selected = (self.selection_start_pos and self.selection_end_pos and 
                              min(self.selection_start_pos[0], self.selection_end_pos[0]) <= i <= 
                              max(self.selection_start_pos[0], self.selection_end_pos[0]))
                              
                if is_selected and text.strip():
                    # Draw selection highlight
                    highlight_rect = pygame.Rect(
                        self.rect.x + 10, 
                        y, 
                        surface_item.get_width() + 10, 
                        max(surface_item.get_height(), self.line_height)
                    )
                    highlight_surface = pygame.Surface((highlight_rect.width, highlight_rect.height), pygame.SRCALPHA)
                    highlight_surface.fill((100, 100, 255, 50))  # Semi-transparent blue
                    surface.blit(highlight_surface, highlight_rect)
                
                if surface_item.get_height() <= 5:  # It's a spacing or separator
                    surface.blit(surface_item, (self.rect.x + 15, y))
                    line_height = surface_item.get_height()
                else:  # Normal text surface
                    surface.blit(surface_item, (self.rect.x + 15, y))
                    line_height = max(surface_item.get_height(), self.line_height)
            elif isinstance(item, pygame.Surface):  # For backwards compatibility
                if item.get_height() <= 5:  # It's a spacing or separator
                    surface.blit(item, (self.rect.x + 15, y))
                    line_height = item.get_height()
                else:  # Normal text surface
                    surface.blit(item, (self.rect.x + 15, y))
                    line_height = max(item.get_height(), self.line_height)
            else:
                print(f"Unexpected item in rendered_lines: {type(item)}")
                
            # Store line position info for mouse selection
            self.line_positions.append((line_y, line_height))
            y += line_height
            
        # Draw copy feedback if active (flash message when text is copied)
        if hasattr(self, 'copy_feedback_timer') and pygame.time.get_ticks() - self.copy_feedback_timer < 1000:
            feedback_text = safe_render("Text copied to clipboard!", font, (100, 255, 100))
            feedback_bg = pygame.Surface((feedback_text.get_width() + 20, feedback_text.get_height() + 10), pygame.SRCALPHA)
            feedback_bg.fill((0, 0, 0, 200))
            feedback_bg.blit(feedback_text, (10, 5))
            surface.blit(feedback_bg, (self.rect.x + 50, self.rect.y + 50))
        
        # Draw scroll indicators if needed
        if self.scroll_position > 0:
            # Draw up arrow
            pygame.draw.polygon(surface, self.text_color, [
                (self.rect.right - 15, self.rect.y + 10),
                (self.rect.right - 5, self.rect.y + 10), 
                (self.rect.right - 10, self.rect.y + 5)
            ])
        
        if self.scroll_position < self.max_scroll:
            # Draw down arrow
            pygame.draw.polygon(surface, self.text_color, [
                (self.rect.right - 15, self.rect.bottom - 10),
                (self.rect.right - 5, self.rect.bottom - 10),
                (self.rect.right - 10, self.rect.bottom - 5)
            ])
        
        # Show instructions for copying text
        instruction_text = "Click+drag to select text, then right-click or Ctrl+C to copy"
        instruction = safe_render(instruction_text, font, (200, 200, 180))
        surface.blit(instruction, (self.rect.x + 20, self.rect.bottom + 5))
        
        # Update this area of the screen immediately to ensure highlights are visible
        pygame.display.update(self.rect)
        pygame.display.update(pygame.Rect(self.rect.x, self.rect.bottom, self.rect.width, 30))

class DialogueSystem:
    def __init__(self):
        self.active = False
        self.current_npc = None
        self.input_text = ""
        self.output_text = ""
        
        # Redesign UI layout to use top half for NPC text
        # Blocks 1+2 (top half): NPC text box
        self.output_rect = pygame.Rect(
            50, 
            SCREEN_HEIGHT // 4, 
            SCREEN_WIDTH - 100, 
            TEXT_OUTPUT_HEIGHT
        )
        
        # Block 3 (third quarter): Player input box - move further down to avoid overlapping with NPC UI
        self.input_rect = pygame.Rect(
            50, 
            3 * SCREEN_HEIGHT // 4 + 30,  # Moved down by 30 pixels
            SCREEN_WIDTH - 100, 
            TEXT_INPUT_HEIGHT
        )
        
        # Voice button next to input box
        self.voice_button_rect = pygame.Rect(
            SCREEN_WIDTH - 70, 
            3 * SCREEN_HEIGHT // 4 + 30,  # Moved down by 30 pixels
            40, 
            40
        )
        
        self.voice_active = False
        self.ai_client = AIServiceClient()
        self.service_status_message = ""
        
        # Create scrollable text box for output
        self.text_box = ScrollableTextBox(
            self.output_rect, 
            font, 
            OUTPUT_BG_COLOR, 
            TEXT_COLOR, 
            TEXT_COLOR
        )
        
        # Check services and set status message
        services_available = self.ai_client.check_services()
        if not services_available:
            if not self.ai_client.asr_available:
                self.service_status_message = "Speech recognition unavailable."
            elif not self.ai_client.npc_ai_available:
                self.service_status_message = "NPC AI unavailable."
            elif not self.ai_client.tts_available:
                self.service_status_message = "Text-to-speech unavailable."
        
        # Initialize clipboard functionality
        self.clipboard_active = False
    
    def activate(self, npc):
        self.active = True
        self.current_npc = npc
        self.input_text = ""
        
        print(f"Activating dialogue with NPC: {npc.name}")
        
        # Just use the predefined initial dialogue - don't try AI yet
        self.output_text = npc.talk()
        self.text_box.set_text(self.output_text)
        
        # Clear any error messages
        self.service_status_message = ""
    
    def deactivate(self):
        self.active = False
        self.current_npc = None
        self.voice_active = False
    
    def handle_input(self, event, player):
        # First let the text box handle scrolling events and text selection
        if self.text_box.handle_event(event):
            return
            
        if event.type == pygame.KEYDOWN:
            # Global keyboard shortcuts
            if event.mod & pygame.KMOD_CTRL:
                if event.key == pygame.K_c:  # Ctrl+C to copy
                    # If text box didn't handle it, try to copy any selected text
                    if self.text_box.selected_text:
                        self.text_box.copy_selected_text()
                        return True
                elif event.key == pygame.K_v:  # Ctrl+V to paste
                    try:
                        clipboard_text = pyperclip.paste()
                        if clipboard_text:
                            self.input_text += clipboard_text
                            print(f"Pasted text: {clipboard_text[:30]}...")
                    except Exception as e:
                        print(f"Failed to paste from clipboard: {e}")
                        traceback.print_exc()
                    return True
                return False
                
            if event.key == pygame.K_ESCAPE:
                # If audio is playing, stop it
                if hasattr(self.ai_client, 'is_playing_audio') and self.ai_client.is_playing_audio:
                    print("Stopping audio playback")
                    self.ai_client.stop_audio()
                    return True
                else:
                    # Otherwise, deactivate the dialogue
                    self.deactivate()
                    return True
                
            if event.key == pygame.K_RETURN:
                # Process input and get response
                if self.input_text.strip():
                    # Try AI first if available
                    if self.ai_client.npc_ai_available:
                        try:
                            ai_response = self.ai_client.get_npc_response(self.current_npc.name, self.input_text)
                            if ai_response:
                                print(f"Response received in handle_input: {ai_response}")
                                # First update the UI with the response text
                                self.output_text = ai_response
                                self.text_box.set_text(ai_response)
                                # Force update the display immediately
                                pygame.display.update(self.output_rect)
                                
                                # Then play audio if available (after UI is updated)
                                if self.ai_client.tts_available:
                                    audio = self.ai_client.text_to_speech(ai_response, self.current_npc.name)
                                    if audio:
                                        # Start audio playback after updating the UI
                                        threading.Thread(target=self.ai_client.play_audio, args=(audio,)).start()
                            else:
                                # Fallback to scripted dialogue
                                self.output_text = self.current_npc.talk(self.input_text)
                                self.text_box.set_text(self.output_text)
                        except Exception as e:
                            print(f"Error getting AI response: {e}")
                            # Fallback to scripted dialogue
                            self.output_text = self.current_npc.talk(self.input_text)
                            self.text_box.set_text(self.output_text)
                    else:
                        # Use scripted dialogue if AI is unavailable
                        self.output_text = self.current_npc.talk(self.input_text)
                        self.text_box.set_text(self.output_text)
                    
                    self.input_text = ""
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            elif event.key == pygame.K_v:
                # Toggle voice input mode if ASR is available and PyAudio is available
                if self.ai_client.asr_available and hasattr(self.ai_client, 'PYAUDIO_AVAILABLE') and self.ai_client.PYAUDIO_AVAILABLE:
                    self.toggle_voice_input()
                else:
                    self.output_text = "Voice input is not available."
                    self.text_box.set_text(self.output_text)
            else:
                self.input_text += event.unicode
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Right-click to copy selected text
            if event.button == 3 and self.text_box.selected_text:
                self.text_box.copy_selected_text()
                return True
                
            # Check if voice button was clicked
            if self.voice_button_rect.collidepoint(event.pos):
                if self.ai_client.asr_available and hasattr(self.ai_client, 'PYAUDIO_AVAILABLE') and self.ai_client.PYAUDIO_AVAILABLE:
                    self.toggle_voice_input()
                else:
                    self.output_text = "Voice input is not available."
                    self.text_box.set_text(self.output_text)
    
    def toggle_voice_input(self):
        """Toggle voice input mode and process voice if activated."""
        if self.voice_active:
            # Already recording, do nothing
            return
            
        self.voice_active = True
        
        # Process voice in a non-blocking way
        try:
            # The process_voice_input now returns a tuple (text, audio)
            response, audio = self.ai_client.process_voice_input(self.current_npc.name)
            
            if response:
                # Update UI first
                self.output_text = response
                self.text_box.set_text(response)
                # Force update
                pygame.display.update(self.output_rect)
                
                # Then play audio if available in a separate thread
                if audio and self.ai_client.tts_available:
                    threading.Thread(target=self.ai_client.play_audio, args=(audio,)).start()
            else:
                self.output_text = "I couldn't understand what you said."
                self.text_box.set_text("I couldn't understand what you said.")
        except Exception as e:
            print(f"Voice input error: {e}")
            traceback.print_exc()
            self.output_text = "I couldn't understand what you said."
            self.text_box.set_text("I couldn't understand what you said.")
        finally:
            self.voice_active = False
    
    def draw(self, screen):
        if self.active:
            # Complete black background instead of semi-transparent overlay
            screen.fill((0, 0, 0))  # Solid black background
            
            # Draw a decorative header bar on top
            header_rect = pygame.Rect(0, 0, SCREEN_WIDTH, 40)
            pygame.draw.rect(screen, (80, 40, 40), header_rect)
            pygame.draw.line(screen, (120, 80, 80), (0, 40), (SCREEN_WIDTH, 40), 2)
            
            # Use our scrollable text box to render the output
            self.text_box.render(screen)
            
            # Draw input box with a nicer style
            pygame.draw.rect(screen, INPUT_BG_COLOR, self.input_rect)
            pygame.draw.rect(screen, (150, 150, 200), self.input_rect, 2)  # Lighter border
            
            # Draw a gradient effect at the top of the input box
            gradient_height = 10
            for i in range(gradient_height):
                alpha = 100 - (i * 100 // gradient_height)
                gradient_line = pygame.Surface((self.input_rect.width, 1), pygame.SRCALPHA)
                gradient_line.fill((255, 255, 255, alpha))
                screen.blit(gradient_line, (self.input_rect.x, self.input_rect.y + i))
            
            # Draw voice input button with a nicer style
            voice_color = VOICE_ACTIVE_COLOR if self.voice_active else (
                VOICE_INACTIVE_COLOR if self.ai_client.asr_available else (100, 20, 20)
            )
            pygame.draw.rect(screen, voice_color, self.voice_button_rect)
            
            # Add gradient to voice button too
            for i in range(gradient_height):
                alpha = 80 - (i * 80 // gradient_height)
                gradient_line = pygame.Surface((self.voice_button_rect.width, 1), pygame.SRCALPHA)
                gradient_line.fill((255, 255, 255, alpha))
                screen.blit(gradient_line, (self.voice_button_rect.x, self.voice_button_rect.y + i))
            
            pygame.draw.rect(screen, (200, 200, 220), self.voice_button_rect, 2)  # Lighter border
            
            # Draw microphone icon in voice button - use safe render for emoji
            try:
                mic_icon = safe_render("🎤", font, TEXT_COLOR)
            except:
                # Fallback if emoji fails
                mic_icon = safe_render("MIC", font, TEXT_COLOR)
            screen.blit(mic_icon, (self.voice_button_rect.x + 10, self.voice_button_rect.y + 10))
            
            # Draw NPC name with special styling
            npc_name_bg = pygame.Rect(
                40, 
                self.output_rect.y - 30, 
                len(self.current_npc.name) * 12 + 40, 
                30
            )
            pygame.draw.rect(screen, (120, 80, 40), npc_name_bg)
            pygame.draw.rect(screen, (180, 140, 80), npc_name_bg, 2)
            
            # Render NPC name with larger font for better visibility
            try:
                npc_name_font = pygame.font.Font(None, FONT_SIZE + 6)
                npc_name_surface = safe_render(f"{self.current_npc.name}", npc_name_font, (255, 255, 200))
            except:
                npc_name_surface = safe_render(f"{self.current_npc.name}", font, (255, 255, 200))
            screen.blit(npc_name_surface, (npc_name_bg.x + 20, npc_name_bg.y + 5))
            
            # Draw "Your input:" label with similar styling
            input_label_bg = pygame.Rect(
                40, 
                self.input_rect.y - 30, 
                120, 
                30
            )
            pygame.draw.rect(screen, (40, 60, 120), input_label_bg)
            pygame.draw.rect(screen, (80, 120, 180), input_label_bg, 2)
            
            you_label = safe_render("Your input:", font, (200, 220, 255))
            screen.blit(you_label, (input_label_bg.x + 20, input_label_bg.y + 5))
            
            # Render input text with cursor with a blinking effect
            cursor_char = '|' if pygame.time.get_ticks() % 1000 < 500 else ' '
            input_surface = safe_render(self.input_text + cursor_char, font, TEXT_COLOR)
            screen.blit(input_surface, (self.input_rect.x + 15, self.input_rect.y + 15))
            
            # Create a single surface for the instruction text to avoid flickering
            if self.voice_active:
                instruction_text = "Listening... (speak clearly)"
            else:
                if self.ai_client.asr_available:
                    instruction_text = "Press ENTER to send, V or click mic to speak, ESC to exit"
                else:
                    instruction_text = "Press ENTER to send, ESC to exit (Voice unavailable)"
                
            # Create a surface for the instruction including its background
            instruction = safe_render(instruction_text, font, TEXT_COLOR)
            instruction_bg = pygame.Surface((instruction.get_width() + 20, instruction.get_height() + 10), pygame.SRCALPHA)
            instruction_bg.fill((0, 0, 0, 200))
            instruction_bg.blit(instruction, (10, 5))
            
            # Position instruction below the input box with more space due to moved down UI
            instruction_y = self.input_rect.y + self.input_rect.height + 10
            screen.blit(instruction_bg, (self.input_rect.x, instruction_y))
            
            # Display service status message if any
            if self.service_status_message:
                status_surface = safe_render(self.service_status_message, font, (255, 100, 100))
                status_bg = pygame.Surface((status_surface.get_width() + 20, status_surface.get_height() + 10), pygame.SRCALPHA)
                status_bg.fill((80, 0, 0, 200))
                status_bg.blit(status_surface, (10, 5))
                
                # Position status message below the instruction text
                status_y = instruction_y + instruction_bg.get_height() + 10
                screen.blit(status_bg, (self.input_rect.x, status_y))
            
            # Draw voice recording indicator if active
            if self.voice_active:
                # Get a reference to the global variables
                global recording_indicator_alpha
                global recording_indicator_increasing
                
                # Create pulsing effect
                if recording_indicator_increasing:
                    recording_indicator_alpha += 5
                    if recording_indicator_alpha >= 230:
                        recording_indicator_increasing = False
                else:
                    recording_indicator_alpha -= 5
                    if recording_indicator_alpha <= 100:
                        recording_indicator_increasing = True
                        
                # Draw recording indicator
                recording_surface = pygame.Surface((SCREEN_WIDTH, 10), pygame.SRCALPHA)
                recording_surface.fill((255, 0, 0, recording_indicator_alpha))
                screen.blit(recording_surface, (0, 0))
                
                # Draw "Recording..." text
                recording_text = safe_render("Recording...", font, (255, 255, 255))
                text_x = SCREEN_WIDTH // 2 - recording_text.get_width() // 2
                screen.blit(recording_text, (text_x, 10))
            
            # Update only the dialogue UI regions instead of the whole screen
            pygame.display.flip()  # Update the entire screen to avoid flicker

def main():
    # Set up dialogue
    hachiko_dialogue = {
        "default": [
            "Woof! I'm not an ordinary dog. I can talk!",
            "I think you should talk to the information booth first.",
            "I smell train station platform attendants nearby! They're responsible for checking tickets.",
            "Trains are so exciting! I can't wait to go for a ride!"
        ],
        "hello": "Hey there! Nice to meet you!",
        "who are you": "I'm your loyal talking companion. Pretty special, right?",
        "help": "You need to speak with the information booth attendant first, then get a ticket, and finally talk to a station platform attendant."
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
    
    sato_dialogue = {
        "default": [
            "Hello! Would you like to purchase a ticket?",
            "That will be $25. Here's your ticket.",
            "Please show your ticket to one of our station platform attendants to board the train.",
            "Have a pleasant journey!"
        ],
        "yes": "Great! Here's your ticket for $25.",
        "how much": "A standard ticket costs $25.",
        "station_platform_attendant": "There are three station platform attendants on duty today. Any one of them can help you board."
    }
    
    tanaka_dialogue = {
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
    
    nakamura_dialogue = {
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
    
    yamada_dialogue = {
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
    hachiko = NPC(MAP_WIDTH // 2 + 50, MAP_HEIGHT // 2, "assets/dog.png", "Hachiko", hachiko_dialogue)  # Changed Dog to Hachiko
    
    # Position NPCs according to the marked locations
    info_attendant = NPC(MAP_WIDTH // 4, MAP_HEIGHT // 4, "assets/info_attendant.png", "Information", info_dialogue)
    sato = NPC(2 * MAP_WIDTH // 3, MAP_HEIGHT // 3, "assets/ticket_attendant.png", "Ticket", sato_dialogue)
    
    # Position station platform attendants - move 1 and 2 up towards track starts
    tanaka = NPC((MAP_WIDTH // 4) - 100, (2 * MAP_HEIGHT // 3) - 100, "assets/conductor1.png", "Station Platform Attendant 1", tanaka_dialogue)  # Moved up
    nakamura = NPC(3 * MAP_WIDTH // 4, (2 * MAP_HEIGHT // 3) - 100, "assets/conductor2.png", "Station Platform Attendant 2", nakamura_dialogue)  # Moved up
    yamada = NPC((MAP_WIDTH // 2) - 100, (3 * MAP_HEIGHT // 4) - 20, "assets/conductor3.png", "Station Platform Attendant 3", yamada_dialogue)  # Keep in middle
    
    # Group NPCs
    npcs = [info_attendant, sato, tanaka, nakamura, yamada, hachiko]
    obstacles = [info_attendant, sato, tanaka, nakamura, yamada]  # Dog is not an obstacle
    
    # Setup dialogue system
    dialogue_system = DialogueSystem()
    
    # Game state
    game_state = STATE_EXPLORING
    camera_x = 0
    camera_y = 0
    
    # Create persistent surfaces for progress text and background to prevent flickering
    progress_surface = None
    progress_bg_surface = None
    last_progress_text = ""
    
    # Main game loop
    running = True
    recording_indicator_alpha = 0  # For pulsing effect
    recording_indicator_increasing = True
    
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
                            if npc.name == "Hachiko" and event.key == pygame.K_j:  # Changed Dog to Hachiko
                                print(f"Activating dialogue with: {npc.name}")
                                dialogue_system.activate(npc)
                                game_state = STATE_DIALOGUE
                                break
                            elif npc.name == "Station Platform Attendant 1" and event.key == pygame.K_e:
                                print(f"Activating dialogue with: {npc.name}")
                                dialogue_system.activate(npc)
                                game_state = STATE_DIALOGUE
                                break
                            elif npc.name == "Station Platform Attendant 2" and event.key == pygame.K_r:
                                print(f"Activating dialogue with: {npc.name}")
                                dialogue_system.activate(npc)
                                game_state = STATE_DIALOGUE
                                break
                            elif npc.name == "Station Platform Attendant 3" and event.key == pygame.K_t:
                                print(f"Activating dialogue with: {npc.name}")
                                dialogue_system.activate(npc)
                                game_state = STATE_DIALOGUE
                                break
                            elif (npc.name == "Information" or npc.name == "Ticket") and event.key == pygame.K_e:
                                print(f"Activating dialogue with: {npc.name}")
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
        
        # Only render the game world when not in dialogue mode
        if game_state != STATE_DIALOGUE:
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
                            key_text = "J"  # Use J for the dog
                        elif npc.name == "Station Platform Attendant 1":
                            key_text = "E"
                        elif npc.name == "Station Platform Attendant 2":
                            key_text = "R"
                        elif npc.name == "Station Platform Attendant 3":
                            key_text = "T"
                        else:
                            key_text = "E"
                        
                        # Make the prompt more visible and clearer for the dog interaction
                        if npc.name == "Hachiko":
                            prompt_text = safe_render(f"Press {key_text} to talk to {npc.name}", font, (255, 255, 0))
                        else:
                            prompt_text = safe_render(f"Press {key_text} to talk to {npc.name}", font, TEXT_COLOR)
                        screen.blit(prompt_text, (npc.x - camera_x, npc.y - camera_y - 20))
            
            # Draw progress indicator only in exploring mode
            progress_text = ""
            if player.progression_state == NEED_INFO:
                progress_text = "Find information about taking a train"
            elif player.progression_state == NEED_TICKET:
                progress_text = "Purchase a ticket for the train"
            elif player.progression_state == NEED_STATION_PLATFORM_ATTENDANT:
                progress_text = "Find a station platform attendant to board the train"
            elif player.progression_state == GAME_COMPLETE:
                progress_text = "Congratulations! You're ready to board the train!"
                
            # Only render the text if it has changed to prevent flickering
            if progress_text != last_progress_text:
                progress_surface = safe_render(progress_text, font, TEXT_COLOR)
                last_progress_text = progress_text
                
                # Create a stable background for the progress text
                if progress_surface:
                    padding = 8
                    progress_bg_surface = pygame.Surface(
                        (progress_surface.get_width() + padding*2, 
                        progress_surface.get_height() + padding*2),
                        pygame.SRCALPHA
                    )
                    progress_bg_surface.fill(PROGRESS_BG_COLOR)
            
            # Draw the progress text with its background
            if progress_surface and progress_bg_surface:
                screen.blit(progress_bg_surface, (5, 5))
                screen.blit(progress_surface, (5 + 8, 5 + 8))  # Apply padding of 8px
        
        # Draw dialogue system if active
        if game_state == STATE_DIALOGUE:
            dialogue_system.draw(screen)
        
        # Update display
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
