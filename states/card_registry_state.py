"""Card registry state - thin wrapper for state management."""

import pygame
from game_context import GameContext
from state_manager import GameState, StateManager
from card_game.card_bookshelf import CardBookshelf


class CardRegistryState(GameState):
    """
    Card registry state wrapper for the state machine.

    This is a thin adapter that instantiates the CardBookshelf engine and delegates
    all game logic to it. The state's only job is to handle state transitions.
    """

    def __init__(self, game_context: GameContext, state_manager: StateManager):
        """
        Initialize card registry state.

        Args:
            game_context: Shared game state
            state_manager: Reference to StateManager for state transitions
        """
        super().__init__(game_context, state_manager)
        self.engine = None

    def enter(self, **kwargs) -> None:
        """
        Called when entering card registry state.

        Instantiates the CardBookshelf engine with the screen reference.

        Args:
            **kwargs: Optional data passed from previous state
        """
        self.engine = CardBookshelf(self.state_manager.screen)

    def exit(self) -> None:
        """
        Called when exiting card registry state.

        Cleans up the CardBookshelf engine instance.
        """
        self.engine = None

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        """
        Delegate event handling to CardBookshelf engine and handle state transitions.

        Args:
            events: List of pygame events
        """
        if self.engine:
            action = self.engine.handle_events(events)
            if action:
                self.state_manager.change_state(action)

    def update(self, dt: float) -> None:
        """
        Delegate update to CardBookshelf engine.

        Args:
            dt: Delta time in seconds
        """
        if self.engine:
            self.engine.update(dt)

    def render(self, screen: pygame.Surface) -> None:
        """
        Delegate rendering to CardBookshelf engine.

        Args:
            screen: Pygame surface to render to
        """
        if self.engine:
            self.engine.render()
