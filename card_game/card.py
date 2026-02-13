"""Card and CardType definitions for card combat."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Optional, TYPE_CHECKING
from card_game.card_registry import register_card

if TYPE_CHECKING:
    from card_game.player import Player

class CardType(Enum):
    """Enumeration of card types in the combat system."""
    ATTACK = "attack"
    DEFENSE = "defense"
    HEAL = "heal"
    SPECIAL = "special"


class Card(ABC):
    """
    Abstract base class for all cards.

    All cards have a name and description. Subclasses implement
    specific card behaviors through the play() method.
    """

    def __init__(self, name: str, description: str, card_type: CardType):
        """
        Initialize a card.

        Args:
            name: Display name of the card
            description: Text description of card effect
            card_type: Type of card (attack, defense, special)
        """
        self.name = name
        self.description = description
        self.card_type = card_type

    @abstractmethod
    def play(self, player: 'Player', target: Optional['Player'] = None) -> None:
        """
        Execute the card's effect.

        Args:
            player: The player playing the card.
            target: The target of the card, if any.
        """
        pass


class BasicAttack(Card):
    """
    Abstract basic attack card that deals damage.

    BasicAttack cards have a damage value and deal that damage
    to the target when played.
    """

    def __init__(self, name: str, description: str, damage: int):
        """
        Initialize a basic attack card.

        Args:
            name: Display name of the card
            description: Text description of card effect
            damage: Amount of damage this card deals
        """
        super().__init__(name, description, CardType.ATTACK)
        self.damage = damage

    def play(self, player: 'Player', target: Optional['Player'] = None) -> None:
        """
        Deal damage to the target.

        Args:
            player: The player using the card.
            target: The target to damage.
        """
        if target:
            target.take_damage(self.damage)


@register_card("kinetic_battle_rifle")
class KineticBattleRifle(BasicAttack):
    """Kinetic Battle Rifle - deals 3 damage."""

    def __init__(self):
        """Initialize Kinetic Battle Rifle card."""
        super().__init__(
            name="Kinetic Battle Rifle",
            description="Deal 3 damage",
            damage=3
        )


@register_card("kinetic_sidearm")
class KineticSidearm(BasicAttack):
    """Kinetic Sidearm - deals 2 damage."""

    def __init__(self):
        """Initialize Kinetic Sidearm card."""
        super().__init__(
            name="Kinetic Sidearm",
            description="Deal 2 damage",
            damage=2
        )


@register_card("knife")
class Knife(BasicAttack):
    """Knife - deals 1 damage."""

    def __init__(self):
        """Initialize Knife card."""
        super().__init__(
            name="Knife",
            description="Deal 1 damage",
            damage=1
        )


class HealCard(Card):
    """Base class for cards that restore health."""
    def __init__(self, name: str, description: str, heal_amount: int):
        super().__init__(name, description, CardType.HEAL)
        self.heal_amount = heal_amount

    def play(self, player: 'Player', target: Optional['Player'] = None) -> None:
        # Heal cards target the player who played them
        player.heal(self.heal_amount)


@register_card("med_patch")
class MedPatch(HealCard):
    """A basic first aid patch that restores 2 HP."""
    def __init__(self):
        super().__init__(
            name="Med Patch",
            description="Restores 2 HP",
            heal_amount=2
        )
