"""Card combat state - thin wrapper for state management."""

import pygame
from game_context import GameContext
from state_manager import GameState, StateManager
from card_game.combat import CardCombat


class CardCombatState(GameState):
    """
    Card combat state wrapper for the state machine.

    This is a thin adapter that instantiates the CardCombat engine and delegates
    all game logic to it. The state's only job is to handle state transitions.
    """

    def __init__(self, game_context: GameContext, state_manager: StateManager):
        """
        Initialize card combat state.

        Args:
            game_context: Shared game state
            state_manager: Reference to StateManager for state transitions
        """
        super().__init__(game_context, state_manager)
        self.engine = None
        self.game_context = game_context

    def enter(self, **kwargs) -> None:
        """
        Called when entering card combat state.

        Instantiates the CardCombat engine with battle parameters.

        Args:
            **kwargs: Optional battle parameters including:
                - enemy_hp: Enemy's maximum hit points (default: 15)
                - enemy_deck: Enemy deck identifier (default: "basic")
                - battle_id: Unique identifier for this battle (default: "default")
                - is_gatekeeper: Whether this is a gatekeeper battle (default: False)
        """
        # Extract battle parameters with defaults
        enemy_hp = kwargs.get('enemy_hp', 15)
        enemy_deck = kwargs.get('enemy_deck', 'basic')
        battle_id = kwargs.get('battle_id', 'default')
        is_gatekeeper = kwargs.get('is_gatekeeper', False)

        # Create CardCombat engine with parameters
        self.engine = CardCombat(
            screen=self.state_manager.screen,
            game_context=self.game_context,
            enemy_hp=enemy_hp,
            enemy_deck=enemy_deck,
            battle_id=battle_id,
            is_gatekeeper=is_gatekeeper
        )

    def exit(self) -> None:
        """
        Called when exiting card combat state.

        Cleans up the CardCombat engine instance.
        """
        self.engine = None

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        """
        Delegate event handling to CardCombat engine and handle state transitions.

        Args:
            events: List of pygame events
        """
        if self.engine:
            action = self.engine.handle_events(events)
            if action:
                self.state_manager.change_state(action)

    def update(self, dt: float) -> None:
        """
        Delegate update to CardCombat engine.

        Args:
            dt: Delta time in seconds
        """
        if self.engine:
            self.engine.update(dt)

    def render(self, screen: pygame.Surface) -> None:
        """
        Delegate rendering to CardCombat engine.

        Args:
            screen: Pygame surface to render to
        """
        if self.engine:
            self.engine.render()
