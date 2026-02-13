"""Deck builder engine for creating and managing decks."""

import pygame
from typing import Optional, Dict
from game_context import GameContext
from card_game.card_registry import create_card


class DeckBuilder:
    """
    Deck builder engine.

    This engine allows players to create and modify decks.
    """

    def __init__(self, screen: pygame.Surface, context: GameContext):
        """
        Initialize the deck builder engine.

        Args:
            screen: Pygame surface for rendering
            context: Game context with player deck
        """
        self.screen = screen
        self.context = context
        self.font = pygame.font.Font(None, 48)
        self.card_font = pygame.font.Font(None, 24)
        self.button_rect = None
        self.mouse_over_button = False

    def _get_card_counts(self) -> Dict[str, tuple]:
        """
        Get unique cards with their counts.

        Returns:
            Dictionary mapping card name to (card_object, count)
        """
        card_counts = {}
        if self.context.player_deck:
            for card in self.context.player_deck:
                if card.name not in card_counts:
                    card_counts[card.name] = (card, 1)
                else:
                    existing_card, count = card_counts[card.name]
                    card_counts[card.name] = (existing_card, count + 1)
        return card_counts

    def handle_events(self, events: list[pygame.event.Event]) -> Optional[str]:
        """
        Handle deck builder input events.

        Args:
            events: List of pygame events

        Returns:
            Action string for state transitions or None
        """
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    if self.button_rect and self.button_rect.collidepoint(event.pos):
                        # Add knife to deck
                        if self.context.player_deck is not None:
                            knife = create_card("knife")
                            self.context.player_deck.append(knife)
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return 'menu'
        return None

    def update(self, dt: float) -> None:
        """
        Update deck builder logic.

        Args:
            dt: Delta time in seconds
        """
        pass

    def render(self) -> None:
        """Render the deck builder screen."""
        # Dark purple background
        self.screen.fill((64, 0, 64))

        # Title
        title_surface = self.font.render("Deck Builder", True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(self.screen.get_width() // 2, 50))
        self.screen.blit(title_surface, title_rect)

        # Instructions
        instructions_surface = self.card_font.render("(ESC for menu)", True, (200, 200, 200))
        instructions_rect = instructions_surface.get_rect(center=(self.screen.get_width() // 2, 100))
        self.screen.blit(instructions_surface, instructions_rect)

        # Display deck
        if not self.context.player_deck:
            no_deck_surface = self.font.render("No deck available", True, (150, 150, 150))
            no_deck_rect = no_deck_surface.get_rect(center=(self.screen.get_width() // 2, 300))
            self.screen.blit(no_deck_surface, no_deck_rect)
        else:
            # Get unique cards with counts
            card_counts = self._get_card_counts()

            # Display cards
            start_y = 150
            card_height = 100
            card_width = 600
            gap = 10
            x = (self.screen.get_width() - card_width) // 2

            for i, (card_name, (card, count)) in enumerate(card_counts.items()):
                y = start_y + (i * (card_height + gap))

                # Card background
                card_rect = pygame.Rect(x, y, card_width, card_height)
                pygame.draw.rect(self.screen, (80, 40, 80), card_rect)
                pygame.draw.rect(self.screen, (200, 100, 200), card_rect, 2)

                # Card name
                name_surface = self.font.render(card.name, True, (255, 255, 100))
                self.screen.blit(name_surface, (x + 10, y + 10))

                # Card type
                type_text = f"Type: {card.card_type.value}"
                type_surface = self.card_font.render(type_text, True, (200, 200, 200))
                self.screen.blit(type_surface, (x + 10, y + 50))

                # Card description
                desc_surface = self.card_font.render(card.description, True, (180, 180, 180))
                self.screen.blit(desc_surface, (x + 10, y + 70))

                # Count
                count_text = f"Count: {count}"
                count_surface = self.card_font.render(count_text, True, (255, 200, 100))
                self.screen.blit(count_surface, (x + 10, y + 75))

                # Damage (if present)
                if hasattr(card, 'damage'):
                    damage_text = f"Damage: {card.damage}"
                    damage_surface = self.font.render(damage_text, True, (255, 100, 100))
                    damage_rect = damage_surface.get_rect(right=x + card_width - 10, centery=y + card_height // 2)
                    self.screen.blit(damage_surface, damage_rect)

            # Add Knife button at bottom
            button_width = 300
            button_height = 60
            button_x = (self.screen.get_width() - button_width) // 2
            button_y = self.screen.get_height() - 100

            self.button_rect = pygame.Rect(button_x, button_y, button_width, button_height)

            # Check mouse hover
            mouse_pos = pygame.mouse.get_pos()
            self.mouse_over_button = self.button_rect.collidepoint(mouse_pos)

            # Button color based on hover
            button_color = (100, 150, 100) if self.mouse_over_button else (60, 100, 60)
            pygame.draw.rect(self.screen, button_color, self.button_rect)
            pygame.draw.rect(self.screen, (150, 255, 150), self.button_rect, 3)

            # Button text
            button_text = "Add Knife To Deck"
            button_surface = self.card_font.render(button_text, True, (255, 255, 255))
            button_text_rect = button_surface.get_rect(center=self.button_rect.center)
            self.screen.blit(button_surface, button_text_rect)
