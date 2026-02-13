"""Save and load game functionality."""

import pygame
import os
import pickle
from typing import Optional, List, Tuple
from game_context import GameContext


class SaveManagement:
    """
    Save management engine.

    This engine handles saving and loading games.
    """

    def __init__(self, screen: pygame.Surface, context: GameContext):
        """
        Initialize the save management engine.

        Args:
            screen: Pygame surface for rendering
            context: Game context to save/load
        """
        self.screen = screen
        self.context = context
        self.font = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 36)
        self.save_dir = "savegames"
        self.message = ""
        self.message_timer = 0.0
        self.selected_index = 0
        self.mouse_over_menu_item = False
        self.mode = "menu"  # "menu" or "load_select"
        self.menu_options = [
            ("S - Save Game", "save"),
            ("L - Load Game", "load"),
            ("ESC - Menu", "menu")
        ]
        self.save_files: List[Tuple[str, str, int]] = []  # (filename, player_name, deck_count)
        
        # Create savegames directory if it doesn't exist
        os.makedirs(self.save_dir, exist_ok=True)

    def _scan_save_files(self) -> None:
        """Scan savegames directory and load metadata from each save file."""
        self.save_files = []
        if not os.path.exists(self.save_dir):
            return
        
        for filename in os.listdir(self.save_dir):
            if filename.endswith('.dat'):
                filepath = os.path.join(self.save_dir, filename)
                try:
                    with open(filepath, 'rb') as f:
                        save_data = pickle.load(f)
                    player_name = save_data.get('player_name', 'Unknown')
                    deck = save_data.get('player_deck', [])
                    deck_count = len(deck) if deck else 0
                    self.save_files.append((filename, player_name, deck_count))
                except Exception:
                    # Skip corrupted save files
                    pass

    def _execute_action(self, action: str) -> Optional[str]:
        """
        Execute a menu action.

        Args:
            action: Action to execute ('save', 'load', or 'menu')

        Returns:
            State transition string or None
        """
        if action == "save":
            if not self.context.player_name:
                self.message = "No active game to save!"
                self.message_timer = 2.0
                return None
            
            try:
                filename = f"{self.context.player_name}.dat"
                filepath = os.path.join(self.save_dir, filename)
                self.context.save(filepath)
                self.message = "Game saved successfully!"
                self.message_timer = 2.0
            except Exception as e:
                self.message = f"Save failed: {e}"
                self.message_timer = 2.0
        elif action == "load":
            # Switch to load select mode
            self._scan_save_files()
            if not self.save_files:
                self.message = "No save files found!"
                self.message_timer = 2.0
            else:
                self.mode = "load_select"
                self.selected_index = 0
        elif action == "menu":
            return "menu"
        elif action == "back":
            # Return to menu mode from load select
            self.mode = "menu"
            self.selected_index = 0
        elif action.startswith("load_file:"):
            # Load specific save file
            filename = action.split(":", 1)[1]
            filepath = os.path.join(self.save_dir, filename)
            try:
                self.context.load(filepath)
                self.message = "Game loaded successfully!"
                self.message_timer = 2.0
                self.mode = "menu"
                self.selected_index = 0
            except Exception as e:
                self.message = f"Load failed: {e}"
                self.message_timer = 2.0
        return None

    def handle_events(self, events: list[pygame.event.Event]) -> Optional[str]:
        """
        Handle save management input events.

        Args:
            events: List of pygame events

        Returns:
            Action string for state transitions or None
        """
        # Get current menu options based on mode
        if self.mode == "load_select":
            current_options = [(f"{name} ({count} cards)", f"load_file:{filename}") 
                             for filename, name, count in self.save_files]
            current_options.append(("Back", "back"))
        else:
            current_options = self.menu_options

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    if self.mouse_over_menu_item:
                        action = current_options[self.selected_index][1]
                        result = self._execute_action(action)
                        if result:
                            return result

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected_index -= 1
                    if self.selected_index < 0:
                        self.selected_index = len(current_options) - 1
                elif event.key == pygame.K_DOWN:
                    self.selected_index += 1
                    if self.selected_index >= len(current_options):
                        self.selected_index = 0
                elif event.key == pygame.K_RETURN:
                    action = current_options[self.selected_index][1]
                    result = self._execute_action(action)
                    if result:
                        return result
                # Legacy key support (only in menu mode)
                elif self.mode == "menu":
                    if event.key == pygame.K_s:
                        return self._execute_action("save")
                    elif event.key == pygame.K_l:
                        return self._execute_action("load")
                    elif event.key == pygame.K_ESCAPE:
                        return self._execute_action("menu")
                # ESC in load_select mode goes back
                elif self.mode == "load_select" and event.key == pygame.K_ESCAPE:
                    self._execute_action("back")
        return None

    def update(self, dt: float) -> None:
        """
        Update save management logic.

        Args:
            dt: Delta time in seconds
        """
        if self.message_timer > 0:
            self.message_timer -= dt

    def render(self) -> None:
        """Render the save management screen."""
        # Dark brown background
        self.screen.fill((64, 48, 32))

        # Title
        if self.mode == "load_select":
            title_text = "Select Save File"
        else:
            title_text = "Save Management"
        
        title_surface = self.font.render(title_text, True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(self.screen.get_width() // 2, 100))
        self.screen.blit(title_surface, title_rect)

        # Current player info (only in menu mode)
        y_offset = 200
        if self.mode == "menu":
            if self.context.player_name:
                player_surface = self.font_small.render(f"Player: {self.context.player_name}", True, (200, 200, 200))
                player_rect = player_surface.get_rect(center=(self.screen.get_width() // 2, y_offset))
                self.screen.blit(player_surface, player_rect)

                deck_count = len(self.context.player_deck) if self.context.player_deck else 0
                deck_surface = self.font_small.render(f"Deck: {deck_count} cards", True, (200, 200, 200))
                deck_rect = deck_surface.get_rect(center=(self.screen.get_width() // 2, y_offset + 50))
                self.screen.blit(deck_surface, deck_rect)
                y_offset = 350
            else:
                no_game_surface = self.font_small.render("No active game", True, (150, 150, 150))
                no_game_rect = no_game_surface.get_rect(center=(self.screen.get_width() // 2, y_offset))
                self.screen.blit(no_game_surface, no_game_rect)
                y_offset = 300
        else:
            y_offset = 200

        # Mouse position
        mouse_pos = pygame.mouse.get_pos()

        # Get current menu options based on mode
        if self.mode == "load_select":
            current_options = [(f"{name} ({count} cards)", f"load_file:{filename}") 
                             for filename, name, count in self.save_files]
            current_options.append(("Back", "back"))
        else:
            current_options = self.menu_options

        # Menu options with rectangles
        rect_width = 400
        rect_height = 60
        gap = 20

        anyrect = False
        for i, (option_text, _) in enumerate(current_options):
            option_surface = self.font_small.render(option_text, True, (255, 255, 255))
            option_rect = option_surface.get_rect(center=(self.screen.get_width() // 2, y_offset))

            # Create fixed-width rectangle centered on screen
            bg_rect = pygame.Rect(
                self.screen.get_width() // 2 - rect_width // 2,
                y_offset - rect_height // 2,
                rect_width,
                rect_height
            )

            # Check if mouse is hovering over menu rectangles and update selection
            if bg_rect.collidepoint(mouse_pos):
                self.selected_index = i
                anyrect = True

            # Use selected_index to determine color
            is_selected = (i == self.selected_index)
            color = (100, 100, 150) if is_selected else (64, 64, 64)
            pygame.draw.rect(self.screen, color, bg_rect)

            self.screen.blit(option_surface, option_rect)
            y_offset += rect_height + gap

        self.mouse_over_menu_item = anyrect

        # Message
        if self.message_timer > 0:
            message_surface = self.font_small.render(self.message, True, (255, 255, 100))
            message_rect = message_surface.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() - 100))
            self.screen.blit(message_surface, message_rect)
