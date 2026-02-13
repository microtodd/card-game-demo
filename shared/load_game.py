"""Load game functionality."""

import pygame
from typing import Optional


class LoadGame:
    """
    Load game engine.

    This engine handles loading saved games.
    """

    def __init__(self, screen: pygame.Surface):
        """
        Initialize the load game engine.

        Args:
            screen: Pygame surface for rendering
        """
        self.screen = screen
        self.font = pygame.font.Font(None, 48)

    def handle_events(self, events: list[pygame.event.Event]) -> Optional[str]:
        """
        Handle load game input events.

        Args:
            events: List of pygame events

        Returns:
            Action string for state transitions or None
        """
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return 'menu'
        return None

    def update(self, dt: float) -> None:
        """
        Update load game logic.

        Args:
            dt: Delta time in seconds
        """
        # TODO: Implement load game logic
        pass

    def render(self) -> None:
        """Render the load game screen."""
        # Dark brown background
        self.screen.fill((64, 48, 32))

        # Title
        title_surface = self.font.render("Load Game", True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(self.screen.get_width() // 2, 100))
        self.screen.blit(title_surface, title_rect)

        # Instructions
        instructions_surface = self.font.render("(ESC for menu)", True, (200, 200, 200))
        instructions_rect = instructions_surface.get_rect(center=(self.screen.get_width() // 2, 200))
        self.screen.blit(instructions_surface, instructions_rect)
