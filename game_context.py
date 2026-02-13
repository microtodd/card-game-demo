"""
Game context for shared state across all game modes.

The GameContext holds all persistent game data (player info, deck, progress, etc.)
that needs to be accessible across different game states. This provides a clean
separation between game state (what's happening in the game) and flow state
(which screen/mode we're in).
"""

import pickle
from typing import Optional, Any, List, Dict, Set


class GameContext:
    """
    Shared game state container.

    This object is passed to all game states and contains all persistent
    game data. States can read and write to this context to share information
    and maintain game progress across state transitions.
    """

    def __init__(self):
        """Initialize game context with default values."""
        self.player_name: Optional[str] = None
        self.player_deck: Optional[Any] = None  # Deck object from card_game.deck

        # Debug mode flag (set by StateManager)
        self.debug_mode: bool = False

        # Progression tracking fields for Alpha 1 game loop
        self.completed_battles: List[str] = []  # Track completed battle IDs
        self.completed_dialogues: List[str] = []  # Track completed dialogue tree IDs
        self.current_milestone: str = "chapter_start"  # Current progression state
        self.battle_attempts: Dict[str, int] = {}  # Track battle attempt counts for difficulty assistance
        
        # Story context for visual novel engine with sensible defaults
        self.context: dict = {
            'player_name': 'Recruit',  # Default name until set
            'reputation': 0,  # Default reputation
            'completed_trees': [],  # Track completed dialogue trees (legacy)
            'choices': {}  # Track player choices
        }

    def _debug_print(self) -> None:
        """Print debug information about the game context."""
        print(f"Player Name: {self.player_name}")
        print(f"Player Deck: {self.player_deck}")
        print(f"Debug Mode: {self.debug_mode}")
        print(f"Completed Battles: {self.completed_battles}")
        print(f"Completed Dialogues: {self.completed_dialogues}")
        print(f"Current Milestone: {self.current_milestone}")
        print(f"Battle Attempts: {self.battle_attempts}")
        print(f"Context: {self.context}")

    def save(self, filename: str) -> None:
        """
        Save game context to file.

        Args:
            filename: Path to save file
        """
        save_data = {
            'player_name': self.player_name,
            'player_deck': self.player_deck,
            'context': self.context,
            # Alpha 1 progression tracking fields
            'completed_battles': self.completed_battles,
            'completed_dialogues': self.completed_dialogues,
            'current_milestone': self.current_milestone,
            'battle_attempts': self.battle_attempts
        }
        with open(filename, 'wb') as f:
            pickle.dump(save_data, f)

    def load(self, filename: str) -> None:
        """
        Load game context from file.

        Args:
            filename: Path to save file
        """
        with open(filename, 'rb') as f:
            save_data = pickle.load(f)
        
        self.player_name = save_data.get('player_name')
        self.player_deck = save_data.get('player_deck')
        
        # Load Alpha 1 progression tracking fields with defaults for backward compatibility
        self.completed_battles = save_data.get('completed_battles', [])
        self.completed_dialogues = save_data.get('completed_dialogues', [])
        self.current_milestone = save_data.get('current_milestone', "chapter_start")
        self.battle_attempts = save_data.get('battle_attempts', {})
        
        # Load context with defaults for missing keys (backward compatibility)
        loaded_context = save_data.get('context', {})
        self.context = {
            'player_name': loaded_context.get('player_name', self.player_name or 'Recruit'),
            'reputation': loaded_context.get('reputation', 0),
            'completed_trees': loaded_context.get('completed_trees', []),
            'choices': loaded_context.get('choices', {})
        }
        # Preserve any additional keys that might have been added
        for key, value in loaded_context.items():
            if key not in self.context:
                self.context[key] = value

    def reset(self) -> None:
        """Reset game context to initial state (for new game)."""
        self.player_name = None
        self.player_deck = None

        # Note: debug_mode is NOT reset here as it's a system-level setting

        # Reset Alpha 1 progression tracking fields
        self.completed_battles = []
        self.completed_dialogues = []
        self.current_milestone = "chapter_start"
        self.battle_attempts = {}
        
        self.context = {
            'player_name': 'Recruit',  # Default name until set
            'reputation': 0,  # Default reputation
            'completed_trees': [],  # Track completed dialogue trees
            'choices': {}  # Track player choices
        }
