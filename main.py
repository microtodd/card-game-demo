"""
Main entry point for the multi-engine game.

This module sets up the pygame window, initializes the state manager,
registers all game states, and runs the main game loop with delta time.
"""

import pygame
import argparse
from game_context import GameContext
from state_manager import StateManager
from states.menu_state import MenuState
from states.card_combat_state import CardCombatState
from states.load_game_state import LoadGameState
from states.deck_builder_state import DeckBuilderState
from states.card_registry_state import CardRegistryState


def main(debug_mode = False):
    """Initialize and run the game."""
    # Initialize pygame
    pygame.init()

    # Set up display (fullscreen)
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("Sci-Fi RPG Card Game")

    # Ensure mouse cursor is visible
    pygame.mouse.set_visible(True)

    # Create clock for delta time tracking
    clock = pygame.time.Clock()
    FPS = 60

    # Create game context (shared state across all game modes)
    context = GameContext()

    # Create state manager with screen reference and debug mode enabled
    state_manager = StateManager(screen, context, debug_mode=debug_mode)

    # Register all game states
    state_manager.register_state('menu', MenuState(context, state_manager))
    state_manager.register_state('card_combat', CardCombatState(context, state_manager))
    state_manager.register_state('load_game', LoadGameState(context, state_manager))
    state_manager.register_state('deck_builder', DeckBuilderState(context, state_manager))
    state_manager.register_state('card_registry', CardRegistryState(context, state_manager))

    # Start at menu state
    state_manager.change_state('menu')

    # Main game loop
    running = True
    while running:
        # Calculate delta time in seconds
        dt = clock.tick(FPS) / 1000.0

        # Event handling
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False

        # Delegate to current state
        state_manager.handle_events(events)
        state_manager.update(dt)
        state_manager.render(screen)

        # Update display
        pygame.display.flip()

    # Clean up
    pygame.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Sci-Fi RPG Card Game.")
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()

    if args.debug:
        print("Debug mode enabled. Game will run in debug mode.")
    main(debug_mode=args.debug)
