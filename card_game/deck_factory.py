"""Factory functions for creating card decks."""

from typing import List
from card_game.card_registry import create_card
from card_game.card import Card


def create_starter_deck() -> List[Card]:
    """
    Create a starter deck for new players.

    Returns:
        List of Card instances representing the starter deck
    """
    deck = []

    # Add 5x Kinetic Sidearm
    for _ in range(5):
        deck.append(create_card("kinetic_sidearm"))

    # Add 5x Knife
    for _ in range(5):
        deck.append(create_card("knife"))

    # Add 2x Kinetic Battle Rifle
    for _ in range(2):
        deck.append(create_card("kinetic_battle_rifle"))

    # Add 2x Med Patch
    for _ in range(2):
        deck.append(create_card("med_patch"))

    # Add 2x Energy Shield (defense)
    for _ in range(2):
        deck.append(create_card("energy_shield"))

    return deck


def create_intro_enemy_deck() -> List[Card]:
    """
    Create an enemy deck for the intro battle.
    
    This deck provides a moderate challenge for new players,
    focusing on basic attacks with some variety.

    Returns:
        List of Card instances representing the intro enemy deck
    """
    deck = []

    # Add 6x Knife (basic low damage)
    for _ in range(6):
        deck.append(create_card("knife"))

    # Add 4x Kinetic Sidearm (medium damage)
    for _ in range(4):
        deck.append(create_card("kinetic_sidearm"))

    # Add 2x Kinetic Battle Rifle (higher damage)
    for _ in range(2):
        deck.append(create_card("kinetic_battle_rifle"))

    return deck


def create_chapter_boss_deck() -> List[Card]:
    """
    Create an enemy deck for the chapter boss battle.
    
    This deck provides a challenging encounter with more powerful cards
    and better composition than the intro battle.

    Returns:
        List of Card instances representing the chapter boss deck
    """
    deck = []

    # Add 3x Knife (some basic attacks)
    for _ in range(3):
        deck.append(create_card("knife"))

    # Add 5x Kinetic Sidearm (solid medium damage)
    for _ in range(5):
        deck.append(create_card("kinetic_sidearm"))

    # Add 4x Kinetic Battle Rifle (heavy damage focus)
    for _ in range(4):
        deck.append(create_card("kinetic_battle_rifle"))

    return deck


def create_grinder_enemy_deck() -> List[Card]:
    """
    Create an enemy deck for optional grinder battles.
    
    This deck provides a balanced challenge for players who want
    to practice and earn rewards without story progression requirements.

    Returns:
        List of Card instances representing the grinder enemy deck
    """
    deck = []

    # Add 5x Knife (basic attacks)
    for _ in range(5):
        deck.append(create_card("knife"))

    # Add 5x Kinetic Sidearm (balanced medium damage)
    for _ in range(5):
        deck.append(create_card("kinetic_sidearm"))

    # Add 2x Kinetic Battle Rifle (some heavy hits)
    for _ in range(2):
        deck.append(create_card("kinetic_battle_rifle"))

    # Add 2x Med Patch
    for _ in range(2):
        deck.append(create_card("med_patch"))

    return deck

def create_test_small_deck() -> List[Card]:
    """
    Create a test deck of 5 cards to test reshuffling.

    Returns:
        List of Card instances representing the starter deck
    """
    deck = []

    # Add 5x Kinetic Sidearm
    for _ in range(5):
        deck.append(create_card("kinetic_sidearm"))

    return deck