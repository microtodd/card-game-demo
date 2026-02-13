"""Main menu state with number key navigation."""

import pygame
from game_context import GameContext
from state_manager import GameState, StateManager


class MenuState(GameState):
    """
    Main menu state for navigating between game modes.

    Displays title and numbered options for each game mode. Number keys
    transition to the corresponding state, ESC quits the game.
    """

    def __init__(self, game_context: GameContext, state_manager: StateManager):
        """
        Initialize menu state.

        Args:
            game_context: Shared game state
            state_manager: Reference to StateManager for state transitions
        """
        super().__init__(game_context, state_manager)
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 36)
        self.selected_index = 0  # Track which menu item is selected
        self.mouse_over_menu_item = False
        self.game_context = game_context
        self.state_manager = state_manager

        self.menu_options = [
            ( "1 - Play Card Combat Demo", "card_combat" ),
            ( "2 - Card Registry", "card_registry" ),
            ( "3 - Deck Builder", "deck_builder" ),
            ( "4 - Save Management", "load_game" ),
            ( "ESC - Quit", "quit" )
        ]

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        """
        Handle menu input events.

        Number keys transition to game modes, ESC quits.

        Args:
            events: List of pygame events
        """
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                match event.button:
                    case 1:  # Left click
                        if self.mouse_over_menu_item:
                            self._change_state( self.menu_options[self.selected_index][1] )

            if event.type == pygame.KEYDOWN:
                match event.key:
                    case pygame.K_1 | pygame.K_2 | pygame.K_3 | pygame.K_4 | pygame.K_5 | pygame.K_6:
                        menu_item = event.key - pygame.K_0 - 1
                        if menu_item < len(self.menu_options):
                            self._change_state( self.menu_options[menu_item][1] )
                    case pygame.K_UP:
                        self.selected_index -= 1
                        if self.selected_index < 0:
                            self.selected_index = len(self.menu_options) - 1
                        if self.selected_index >= len(self.menu_options):
                            self.selected_index = 0
                    case pygame.K_DOWN:
                        self.selected_index += 1
                        if self.selected_index < 0:
                            self.selected_index = len(self.menu_options) - 1
                        if self.selected_index >= len(self.menu_options):
                            self.selected_index = 0
                    case pygame.K_RETURN:
                        self._change_state( self.menu_options[self.selected_index][1] ) 
                    case pygame.K_ESCAPE:
                        self._change_state( "quit" )

    def _change_state(self, state_name: str) -> None:
        """
        Change to a new state.

        Args:
            state_name: Name of the state to transition to
        """
        if state_name == "new_game":
            self.state_manager.change_state(state_name,
                game_context=self.game_context,
                state_manager=self.state_manager
            )
        else:
            self.state_manager.change_state(state_name)

    def update(self, dt: float) -> None:
        """
        Update menu state.

        Args:
            dt: Delta time in seconds
        """
        pass

    def render(self, screen: pygame.Surface) -> None:
        """
        Render the main menu.

        Displays title and navigation options on black background.

        Args:
            screen: Pygame surface to render to
        """
        # Black background
        screen.fill((0, 0, 0))

        # Title
        title_surface = self.font_large.render("Main Menu", True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(screen.get_width() // 2, 100))
        screen.blit(title_surface, title_rect)

        # Mouse
        mouse_pos = pygame.mouse.get_pos()

        # Menu options
        options = [option[0] for option in self.menu_options]

        # Fixed width for all menu rectangles
        rect_width = 400
        rect_height = 60
        gap = 20  # Vertical spacing between menu items
        padding = 20

        y_offset = 250
        anyrect = False
        for i, option in enumerate(options):
            option_surface = self.font_medium.render(option, True, (255, 255, 255))
            option_rect = option_surface.get_rect(center=(screen.get_width() // 2, y_offset))

            # Draw background rectangle for menu option
            if option:  # Skip drawing rectangle for empty strings
                # Create fixed-width rectangle centered on screen
                bg_rect = pygame.Rect(
                    screen.get_width() // 2 - rect_width // 2,
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
                pygame.draw.rect(screen, color, bg_rect)

            screen.blit(option_surface, option_rect)
            y_offset += rect_height + gap
    
        self.mouse_over_menu_item = anyrect 
