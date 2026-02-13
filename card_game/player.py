"""Player and hand management for card combat."""

import random
from typing import List, Optional
from card_game.card import Card


class Player:
    """
    Represents a player or enemy in the card combat game.

    Tracks health, hand, deck, and provides methods for damage/healing.
    """

    def __init__(self, name: str, max_hit_points: int = 20):
        """
        Initialize a player.

        Args:
            name: Display name of this player/enemy
            max_hit_points: Maximum HP (also starting HP)
        """
        self.name = name
        self.max_hit_points = max_hit_points
        self.hit_points = max_hit_points
        self.hand: List[Card] = []
        self.deck: List[Card] = []
        self.discard_pile: List[Card] = []

    def take_damage(self, amount: int) -> int:
        """
        Take damage and reduce HP.

        Args:
            amount: Amount of damage to take

        Returns:
            Actual damage taken (can't go below 0 HP)
        """
        actual_damage = min(amount, self.hit_points)
        self.hit_points -= actual_damage
        return actual_damage

    def heal(self, amount: int) -> int:
        """
        Heal HP up to maximum.

        Args:
            amount: Amount to heal

        Returns:
            Actual HP healed (can't exceed max)
        """
        actual_healing = min(amount, self.max_hit_points - self.hit_points)
        self.hit_points += actual_healing
        return actual_healing

    def is_alive(self) -> bool:
        """
        Check if player is still alive.

        Returns:
            True if HP > 0, False otherwise
        """
        return self.hit_points > 0

    def is_defeated(self) -> bool:
        """
        Check if player is defeated.

        Returns:
            True if HP <= 0, False otherwise
        """
        return self.hit_points <= 0

    def draw_card(self) -> Optional[Card]:
        """
        Draw a card from deck to hand.

        Returns:
            The drawn card, or None if deck is empty
        """
        if not self.deck:
            return None

        card = self.deck.pop(0)
        self.hand.append(card)
        return card

    def play_card(self, card_index: int, target: 'Player') -> Optional[Card]:
        """
        Play a card from hand.

        Args:
            card_index: Index of card in hand
            target: Target player/enemy for the card

        Returns:
            The played card, or None if invalid index
        """
        if card_index < 0 or card_index >= len(self.hand):
            return None

        card = self.hand.pop(card_index)
        card.play(target)
        self.discard_pile.append(card)
        return card

    def shuffle_deck(self) -> None:
        """
        Shuffle the deck in place.
        """
        random.shuffle(self.deck)

    def reset_deck(self) -> None:
        """
        Reset the deck by collecting all cards from hand and discard pile.

        Moves all cards from hand and discard pile back into the deck.
        Does not automatically shuffle.
        """
        # Move all cards from hand to deck
        self.deck.extend(self.hand)
        self.hand.clear()

        # Move all cards from discard pile to deck
        self.deck.extend(self.discard_pile)
        self.discard_pile.clear()

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"Player({self.name}, HP: {self.hit_points}/{self.max_hit_points})"
