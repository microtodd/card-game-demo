"""Card registration system for auto-registering card classes."""

from typing import Dict, Type, Any, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from card_game.card import Card

# Module-level registry of all card classes
CARD_REGISTRY: Dict[str, Type['Card']] = {}


def register_card(card_id: str) -> Callable:
    """
    Decorator to auto-register card classes in the card registry.

    Args:
        card_id: Unique identifier for this card type

    Returns:
        Decorator function that registers the card class

    Example:
        @register_card("kinetic_battle_rifle")
        class KineticBattleRifle(BasicAttack):
            ...
    """
    def decorator(card_class: Type['Card']) -> Type['Card']:
        """Register the card class and return it unchanged."""
        CARD_REGISTRY[card_id] = card_class
        return card_class
    return decorator


def create_card(card_id: str) -> 'Card':
    """
    Factory function to create a card instance by its ID.

    Args:
        card_id: The unique identifier for the card type

    Returns:
        New instance of the requested card

    Raises:
        ValueError: If card_id is not registered
    """
    if card_id not in CARD_REGISTRY:
        raise ValueError(f"Card ID '{card_id}' not found in registry. Available cards: {list(CARD_REGISTRY.keys())}")

    card_class = CARD_REGISTRY[card_id]
    return card_class()


def get_all_card_ids() -> list[str]:
    """
    Get list of all registered card IDs.

    Returns:
        List of card ID strings
    """
    return list(CARD_REGISTRY.keys())


def get_card_info(card_id: str) -> dict[str, Any]:
    """
    Get card metadata without instantiating the card.

    Args:
        card_id: The unique identifier for the card type

    Returns:
        Dictionary containing card metadata (name, description, etc.)

    Raises:
        ValueError: If card_id is not registered
    """
    if card_id not in CARD_REGISTRY:
        raise ValueError(f"Card ID '{card_id}' not found in registry. Available cards: {list(CARD_REGISTRY.keys())}")

    # Create temporary instance to get metadata
    card = create_card(card_id)

    info = {
        "card_id": card_id,
        "name": card.name,
        "description": card.description,
        "card_type": card.card_type.value,
    }

    # Add damage if it's an attack card
    if hasattr(card, 'damage'):
        info["damage"] = card.damage

    return info
