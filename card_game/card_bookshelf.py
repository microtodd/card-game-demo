"""Card bookshelf engine for browsing available cards."""

import pygame
from typing import Optional
from card_game.card_registry import get_all_card_ids, get_card_info


class CardBookshelf:
    """
    Card bookshelf engine.

    This engine allows players to browse and view all available cards.
    """

    def __init__(self, screen: pygame.Surface):
        """
        Initialize the card bookshelf engine.

        Args:
            screen: Pygame surface for rendering
        """
        self.screen = screen
        self.font = pygame.font.Font(None, 48)
        self.card_font = pygame.font.Font(None, 24)

        # Load all card metadata
        self.card_ids = get_all_card_ids()
        self.card_infos = [get_card_info(card_id) for card_id in self.card_ids]

    def handle_events(self, events: list[pygame.event.Event]) -> Optional[str]:
        """
        Handle card bookshelf input events.

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
        Update card bookshelf logic.

        Args:
            dt: Delta time in seconds
        """
        # TODO: Implement card bookshelf logic
        pass

    def render(self) -> None:
        """Render the card bookshelf screen."""
        # Dark teal background
        self.screen.fill((0, 64, 64))

        # Title
        title_surface = self.font.render("Card Bookshelf", True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(self.screen.get_width() // 2, 50))
        self.screen.blit(title_surface, title_rect)

        # Instructions
        instructions_surface = self.card_font.render("(ESC for menu)", True, (200, 200, 200))
        instructions_rect = instructions_surface.get_rect(center=(self.screen.get_width() // 2, 100))
        self.screen.blit(instructions_surface, instructions_rect)

        # Display all cards
        start_y = 150
        card_height = 100
        card_width = 600
        gap = 10
        x = (self.screen.get_width() - card_width) // 2

        for i, card_info in enumerate(self.card_infos):
            y = start_y + (i * (card_height + gap))

            # Card background
            card_rect = pygame.Rect(x, y, card_width, card_height)
            pygame.draw.rect(self.screen, (40, 80, 80), card_rect)
            pygame.draw.rect(self.screen, (100, 200, 200), card_rect, 2)

            # Card name
            name_surface = self.font.render(card_info['name'], True, (255, 255, 100))
            self.screen.blit(name_surface, (x + 10, y + 10))

            # Card type
            type_text = f"Type: {card_info['card_type']}"
            type_surface = self.card_font.render(type_text, True, (200, 200, 200))
            self.screen.blit(type_surface, (x + 10, y + 50))

            # Card description
            desc_surface = self.card_font.render(card_info['description'], True, (180, 180, 180))
            self.screen.blit(desc_surface, (x + 10, y + 70))

            # Damage (if present)
            if 'damage' in card_info:
                damage_text = f"Damage: {card_info['damage']}"
                damage_surface = self.font.render(damage_text, True, (255, 100, 100))
                damage_rect = damage_surface.get_rect(right=x + card_width - 10, centery=y + card_height // 2)
                self.screen.blit(damage_surface, damage_rect)
