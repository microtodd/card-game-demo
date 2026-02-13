"""Deck builder state - thin wrapper for state management."""

import pygame
from game_context import GameContext
from state_manager import GameState, StateManager
from card_game.deck_builder import DeckBuilder


class DeckBuilderState(GameState):
    """
    Deck builder state wrapper for the state machine.

    This is a thin adapter that instantiates the DeckBuilder engine and delegates
    all game logic to it. The state's only job is to handle state transitions.
    """

    def __init__(self, game_context: GameContext, state_manager: StateManager):
        """
        Initialize deck builder state.

        Args:
            game_context: Shared game state
            state_manager: Reference to StateManager for state transitions
        """
        super().__init__(game_context, state_manager)
        self.engine = None

    def enter(self, **kwargs) -> None:
        """
        Called when entering deck builder state.

        Instantiates the DeckBuilder engine with the screen reference and context.

        Args:
            **kwargs: Optional data passed from previous state
        """
        self.engine = DeckBuilder(self.state_manager.screen, self.context)

    def exit(self) -> None:
        """
        Called when exiting deck builder state.

        Cleans up the DeckBuilder engine instance.
        """
        self.engine = None

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        """
        Delegate event handling to DeckBuilder engine and handle state transitions.

        Args:
            events: List of pygame events
        """
        if self.engine:
            action = self.engine.handle_events(events)
            if action:
                self.state_manager.change_state(action)

    def update(self, dt: float) -> None:
        """
        Delegate update to DeckBuilder engine.

        Args:
            dt: Delta time in seconds
        """
        if self.engine:
            self.engine.update(dt)

    def render(self, screen: pygame.Surface) -> None:
        """
        Delegate rendering to DeckBuilder engine.

        Args:
            screen: Pygame surface to render to
        """
        if self.engine:
            self.engine.render()
