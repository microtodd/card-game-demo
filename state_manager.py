"""
State management system for multi-engine game.

The StateManager coordinates transitions between different game states (menu, combat, VN, hub)
using a state machine pattern. Each state inherits from GameState and implements the standard
interface for event handling, updates, and rendering.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any, TYPE_CHECKING
import pickle
import pygame

if TYPE_CHECKING:
    from game_context import GameContext   

class GameState(ABC):
    """
    Abstract base class for all game states.

    States represent different screens or modes in the game (menu, combat, visual novel, etc).
    Each state handles its own events, updates, and rendering independently.
    """

    def __init__(self, game_context: 'GameContext', state_manager: 'StateManager'):
        """
        Initialize the game state.

        Args:
            game_context: Shared game state (player data, deck, progress, etc.)
            state_manager: Reference to the StateManager for triggering state transitions
        """
        self.context = game_context
        self.state_manager = state_manager

    @abstractmethod
    def handle_events(self, events: list[pygame.event.Event]) -> None:
        """
        Process input events for this state.

        Args:
            events: List of pygame events to process
        """
        pass

    @abstractmethod
    def update(self, dt: float) -> None:
        """
        Update state logic.

        Args:
            dt: Delta time in seconds since last frame
        """
        pass

    @abstractmethod
    def render(self, screen: pygame.Surface) -> None:
        """
        Render this state to the screen.

        Args:
            screen: Pygame surface to render to
        """
        pass

    def enter(self, **kwargs) -> None:
        """
        Called when transitioning into this state.

        Override to set up state-specific resources or handle transition data.

        Args:
            **kwargs: Optional data passed from previous state
        """
        pass

    def exit(self) -> None:
        """
        Called when transitioning out of this state.

        Override to clean up state-specific resources.
        """
        pass

    def get_save_data(self) -> Dict[str, Any]:
        """
        Return state data for save file persistence.

        Returns:
            Dictionary of serializable state data
        """
        return {}

    def load_save_data(self, data: Dict[str, Any]) -> None:
        """
        Restore state from save file data.

        Args:
            data: Dictionary of state data from save file
        """
        pass


class StateManager:
    """
    Manages game states and coordinates transitions between them.

    The StateManager maintains a registry of available states and handles the current
    active state. It coordinates the enter/exit hooks when transitioning and delegates
    event handling, updates, and rendering to the current state.
    """

    def __init__(self, screen: pygame.Surface, game_context: 'GameContext', debug_mode: bool = False):
        """
        Initialize the state manager.

        Args:
            screen: Pygame display surface for rendering
            game_context: Shared game state container
            debug_mode: Enable debug overlays and error messages
        """
        self.screen = screen
        self.context = game_context
        self.states: Dict[str, GameState] = {}
        self.current_state: Optional[GameState] = None
        self.current_state_name: Optional[str] = None

        # Debug mode settings
        self.debug_mode = debug_mode
        self.context.debug_mode = debug_mode  # Share debug mode with all states via context
        self.error_message: Optional[str] = None
        self.error_timer: float = 0.0

        # Register "quit"
        self.register_state("quit", None)

    def register_state(self, name: str, state: GameState) -> None:
        """
        Register a state with the manager.

        Args:
            name: Identifier for this state (e.g., "menu", "combat")
            state: GameState instance to register
        """
        self.states[name] = state

    def change_state(self, name: str, **kwargs) -> None:
        """
        Transition to a different state.

        Calls exit() on the current state and enter() on the new state.

        Args:
            name: Name of the state to transition to
            **kwargs: Optional data to pass to the new state's enter() method
        """
        if self.debug_mode:
            print(f"Switching to {name} with kwargs: {kwargs}")
        if name not in self.states:
            # Show error in debug mode
            self.error_message = f"Invalid state: '{name}'"
            self.error_timer = 1.0
            return

        # Exit current state
        if self.current_state:
            self.current_state.exit()

        # Transition to new state

        # Check for quit
        if name == "quit":
            pygame.event.post(pygame.event.Event(pygame.QUIT))
            return

        # Handle None states by just staying in the current state
        if name is None or name == "":
            return

        # Otherwise switch to new state
        self.current_state = self.states[name]
        self.current_state_name = name
        self.current_state.enter(**kwargs)

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        """
        Delegate event handling to the current state.

        Args:
            events: List of pygame events
        """
        if self.current_state:
            self.current_state.handle_events(events)

    def update(self, dt: float) -> None:
        """
        Delegate update logic to the current state.

        Args:
            dt: Delta time in seconds
        """
        if self.current_state:
            self.current_state.update(dt)

        # Update error timer
        if self.error_timer > 0:
            self.error_timer -= dt

    def render(self, screen: pygame.Surface) -> None:
        """
        Delegate rendering to the current state.

        Args:
            screen: Pygame surface to render to
        """
        if self.current_state:
            self.current_state.render(screen)

        # Render debug error overlay
        if self.debug_mode and self.error_message and self.error_timer > 0:
            # Semi-transparent dark overlay
            overlay = pygame.Surface(screen.get_size())
            overlay.set_alpha(200)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))

            # Error message box
            font = pygame.font.Font(None, 48)
            text = font.render(self.error_message, True, (255, 50, 50))
            text_rect = text.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))

            # Background for text
            padding = 20
            bg_rect = text_rect.inflate(padding * 2, padding * 2)
            pygame.draw.rect(screen, (100, 0, 0), bg_rect)
            pygame.draw.rect(screen, (255, 0, 0), bg_rect, 3)

            # Draw text
            screen.blit(text, text_rect)
