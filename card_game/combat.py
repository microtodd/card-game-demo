"""Card combat game engine."""

import pygame
from enum import Enum
from typing import Optional, Tuple
from game_context import GameContext
from card_game.player import Player
from card_game.deck_factory import create_starter_deck, create_intro_enemy_deck, create_chapter_boss_deck, create_grinder_enemy_deck, create_test_small_deck
from card_game.card import Card, CardType


class CombatState(Enum):
    """States for the combat state machine."""
    PLAYER_TURN = "player_turn"
    PLAYER_DISCARDING = "player_discarding"
    PLAYER_CARD_ANIMATING = "player_card_animating"
    ENEMY_THINKING = "enemy_thinking"
    ENEMY_CARD_ANIMATING = "enemy_card_animating"
    ENEMY_DISCARD_ANIMATING = "enemy_discard_animating"
    WAITING_FOR_COUNTER = "waiting_for_counter"
    COUNTER_ANIMATING = "counter_animating"
    WAITING_FOR_RESOLVE = "waiting_for_resolve"
    RESOLVE_WITH_COUNTER = "resolve_with_counter"
    RESHUFFLING = "reshuffling"
    VICTORY = "victory"
    DEFEAT = "defeat"


class CardAnimation:
    """Represents a card animation from one position to another."""

    def __init__(self, card: Card, card_index: int, start_pos: Tuple[int, int], end_pos: Tuple[int, int], duration: float):
        """
        Initialize a card animation.

        Args:
            card: The card being animated
            card_index: Original index in hand
            start_pos: Starting (x, y) position
            end_pos: Ending (x, y) position
            duration: Animation duration in seconds
        """
        self.card = card
        self.card_index = card_index
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.duration = duration
        self.elapsed = 0.0

    def update(self, dt: float) -> bool:
        """
        Update animation progress.

        Args:
            dt: Delta time in seconds

        Returns:
            True if animation is complete, False otherwise
        """
        self.elapsed += dt
        return self.elapsed >= self.duration

    def get_current_pos(self) -> Tuple[int, int]:
        """
        Get current interpolated position.

        Returns:
            Current (x, y) position
        """
        t = min(self.elapsed / self.duration, 1.0)
        x = int(self.start_pos[0] + (self.end_pos[0] - self.start_pos[0]) * t)
        y = int(self.start_pos[1] + (self.end_pos[1] - self.start_pos[1]) * t)
        return (x, y)


class CardCombat:
    """
    Card combat game engine.

    This engine manages all card combat gameplay including
    mechanics, player hands, decks, and combat resolution. It's independent
    of the state machine.
    """

    def __init__(self, screen: pygame.Surface, game_context: GameContext, enemy_hp: int = 15, enemy_deck: str = "basic", battle_id: str = "default", is_gatekeeper: bool = False):
        """
        Initialize the card combat engine.

        Args:
            screen: Pygame surface for rendering
            game_context: Game context for shared state
            enemy_hp: Enemy's maximum hit points
            enemy_deck: Enemy deck identifier
            battle_id: Unique identifier for this battle
            is_gatekeeper: Whether this is a gatekeeper battle
        """
        self.screen = screen
        self.font = pygame.font.Font(None, 48)
        self.card_font = pygame.font.Font(None, 24)

        # Grab context
        self.game_context = game_context

        # Store battle configuration
        if battle_id == "default" and self.game_context.debug_mode:
            battle_id = "debug"
        self.battle_id = battle_id
        self.is_gatekeeper = is_gatekeeper

        # Create player with starter deck
        self.player = Player("Player", max_hit_points=20)

        # Create enemy with configured HP
        self.enemy = Player("Opponent", max_hit_points=enemy_hp)

        # Initialize player's deck with starter deck
        self.player.deck = create_starter_deck()
        self.player.shuffle_deck()

        # Initialize enemy deck based on configuration
        self._initialize_enemy_deck(enemy_deck)

        # Grab deck sizes
        self.player_deck_size = len(self.player.deck)
        self.enemy_deck_size = len(self.enemy.deck)

        # Give enemy an initial hand
        for _ in range(5):
            self.enemy.draw_card()

        # Track hovered card and draw button
        self.hovered_card_index = None
        self.draw_button_hovered = False
        self.pass_button_hovered = False
        self.discard_button_hovered = False
        self.discard_cards_hovered = {
            0: False,
            1: False,
            2: False,
            3: False,
            4: False
        }

        # Debug buttons
        self.debug_win_button_hovered = False
        self.debug_lose_button_hovered = False

        # Turn counter
        self.turn = 1
        self.round = 1

        # Combat state machine
        self.state = CombatState.PLAYER_TURN

        # Overlays/modifiers (not part of main state)
        self.exit_confirmation_modal = False
        self.last_stand_active = False

        # Animation and staging system
        self.active_animations = []
        self.staged_card = None
        self.staged_card_index = None
        self.staged_card_owner = None  # "player" or "enemy"
        self.returning_card = None  # Card being animated back to hand
        self.returning_card_index = None
        self.discard_cancel_hover = False
        self.discard_confirm_hover = False

        # Enemy turn timing
        self.enemy_think_timer = 0.0
        self.enemy_think_duration = 1.5  # seconds
        self.enemy_discarding_card = None  # Track card being discarded by AI

        # Reshuffle system
        self.reshuffle_timer = 0.0
        self.reshuffle_duration = 2.0  # seconds
        self.reshuffle_target = None  # "player" or "enemy" - who is reshuffling
        self.reshuffle_owner = None  # "player" or "enemy" - whose turn just ended

        # Counter system
        self.counter_card = None  # Selected defense card
        self.counter_card_index = None
        self.skip_counter_hovered = False

    def _initialize_enemy_deck(self, enemy_deck: str) -> None:
        """
        Initialize enemy deck based on deck identifier.

        Args:
            enemy_deck: Deck identifier string
        """
        match enemy_deck:
            case "intro_enemy":
                self.enemy.deck = create_intro_enemy_deck()
                self.ai_persona = "balanced"
            case "chapter_boss":
                self.enemy.deck = create_chapter_boss_deck()
                self.ai_persona = "aggressive"
            case "grinder_enemy":
                self.enemy.deck = create_grinder_enemy_deck()
                self.ai_persona = "balanced"
            case _:
                # Default to intro enemy deck for unknown identifiers
                self.enemy.deck = create_intro_enemy_deck()
                self.ai_persona = "balanced"

        # Shuffle the enemy deck
        self.enemy.shuffle_deck()

    def handle_events(self, events: list[pygame.event.Event]) -> Optional[str]:
        """
        Handle card combat input events.

        Args:
            events: List of pygame events

        Returns:
            Action string for state transitions ('menu', etc.) or None
        """
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Toggle exit confirmation modal
                    self.exit_confirmation_modal = not self.exit_confirmation_modal

                elif event.key == pygame.K_RETURN and self.exit_confirmation_modal:
                    return 'menu'

                elif event.key == pygame.K_SPACE and self.state in (CombatState.VICTORY, CombatState.DEFEAT):
                    return self._after_combat()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                result = self._handle_click(event.pos)
                if result:
                    return result

        return None

    def _handle_click(self, pos: Tuple[int, int]) -> Optional[str]:
        """Handle mouse click based on current state."""
        match self.state:
            case CombatState.VICTORY | CombatState.DEFEAT:
                return self._after_combat()

            case CombatState.WAITING_FOR_RESOLVE | CombatState.RESOLVE_WITH_COUNTER:
                self._handle_resolve_click(pos)

            case CombatState.WAITING_FOR_COUNTER:
                self._handle_counter_click(pos)

            case CombatState.PLAYER_TURN:
                self._handle_player_turn_click(pos)

            case CombatState.PLAYER_DISCARDING:
                self._handle_discard_click(pos)

            case _:
                # Other states don't respond to clicks
                pass

        return None

    def _handle_resolve_click(self, pos: Tuple[int, int]) -> None:
        """Handle clicks during resolve state."""
        layout = self._get_card_layout()
        card_width = layout['card_width']
        card_height = layout['card_height']
        staging_x = (self.screen.get_width() - card_width) // 2
        staging_y = (self.screen.get_height() - card_height) // 2

        staged_card_rect = pygame.Rect(staging_x, staging_y, card_width, card_height)

        # Resolve box is positioned relative to card
        resolve_box_x = staging_x + card_width + 40
        resolve_box_y = staging_y + card_height // 2
        resolve_rect = pygame.Rect(resolve_box_x, resolve_box_y - 40, 200, 80)

        if resolve_rect.collidepoint(pos):
            self._resolve_staged_card()
        elif staged_card_rect.collidepoint(pos) and self.staged_card_owner == "player":
            # Only player can cancel their own cards
            self._cancel_staged_card()

    def _handle_counter_click(self, pos: Tuple[int, int]) -> None:
        """Handle clicks during counter selection."""
        layout = self._get_card_layout()

        # Check if skip button was clicked
        skip_button_rect = self._get_skip_counter_button_rect(layout)
        if skip_button_rect.collidepoint(pos):
            self.state = CombatState.WAITING_FOR_RESOLVE
            return

        # Check if draw button was clicked (uses existing action button)
        if self.draw_button_hovered and len(self.player.hand) < 5:
            # Draw card
            self.player.draw_card()
            # Stay in WAITING_FOR_COUNTER - player can now choose from new cards
            return

        # Check if a defense card in hand was clicked
        for i, card in enumerate(self.player.hand):
            if card.card_type == CardType.DEFENSE:
                card_x = layout['start_x'] + (i * (layout['card_width'] + layout['gap']))
                card_rect = pygame.Rect(card_x, layout['card_y'] - layout['hover_lift'],
                                       layout['card_width'], layout['card_height'])
                if card_rect.collidepoint(pos):
                    # Select this defense card as counter and animate it
                    self.counter_card = self.player.hand.pop(i)
                    self.counter_card_index = i
                    self._start_counter_animation()
                    break

    def _start_counter_animation(self) -> None:
        """Start animation for the counter card moving to staging area."""
        layout = self._get_card_layout()
        card_width = layout['card_width']
        card_height = layout['card_height']

        # Start position: where the card was in hand
        start_x = layout['start_x'] + (self.counter_card_index * (card_width + layout['gap']))
        start_y = layout['card_y'] - layout['hover_lift']
        start_pos = (start_x, start_y)

        # End position: offset from the attack card (to the left)
        staging_x = (self.screen.get_width() - card_width) // 2
        staging_y = (self.screen.get_height() - card_height) // 2
        end_pos = (staging_x - card_width - 20, staging_y)

        animation = CardAnimation(self.counter_card, self.counter_card_index, start_pos, end_pos, 0.2)
        self.active_animations.append(animation)
        self.state = CombatState.COUNTER_ANIMATING

    def _handle_player_turn_click(self, pos: Tuple[int, int]) -> None:
        """Handle clicks during player's turn."""
        # Check debug buttons
        if self.game_context.debug_mode:
            if self.debug_win_button_hovered:
                self._debug_auto_win()
                return
            elif self.debug_lose_button_hovered:
                self._debug_auto_lose()
                return

        # Check draw button
        if self.draw_button_hovered and not self.last_stand_active:
            self.player.draw_card()
            return

        # Check pass button
        if self.pass_button_hovered:
            if self.last_stand_active:
                self.state = CombatState.DEFEAT
                self._handle_combat_completion("defeat")
            else:
                self._start_enemy_turn()
            return

        # Check discard button
        if self.discard_button_hovered and not self.last_stand_active:
            self._start_discard_select()
            return

        # Check if a card was clicked
        if self.hovered_card_index is not None and self.hovered_card_index < len(self.player.hand):
            card = self.player.hand[self.hovered_card_index]
            if self.last_stand_active:
                # In Last Stand, only Heal cards are playable
                if hasattr(card, 'card_type') and card.card_type.value == 'heal':
                    self._start_card_animation(self.hovered_card_index)
            else:
                if hasattr(card, 'card_type') and card.card_type.value in ['attack', 'heal']:
                    self._start_card_animation(self.hovered_card_index)

    def _handle_discard_click(self, pos: Tuple[int, int]) -> None:
        """Handle clicks during discard selection."""
        if self.discard_cancel_hover:
            self.state = CombatState.PLAYER_TURN
            self.discard_cards_hovered = {i: False for i in range(5)}
            return

        # Check if a card was selected for discard
        if self.hovered_card_index is not None and self.hovered_card_index < len(self.player.hand):
            self.discard_cards_hovered[self.hovered_card_index] = not self.discard_cards_hovered[self.hovered_card_index]
            return

        # Check if confirm button clicked
        if self.discard_confirm_hover:
            if not any(self.discard_cards_hovered.values()):
                return  # No cards selected

            for i in reversed(range(5)):
                if self.discard_cards_hovered[i]:
                    self.player.discard_pile.append(self.player.hand.pop(i))

            self.discard_cards_hovered = {i: False for i in range(5)}
            self._start_enemy_turn()

    def _start_card_animation(self, card_index: int, owner: str = "player") -> None:
        """
        Start animation for a card from hand to staging area.

        Args:
            card_index: Index of card in player's or enemy's hand
            owner: "player" or "enemy"
        """
        # Remove card from appropriate hand
        if owner == "player":
            card = self.player.hand.pop(card_index)
        else:  # enemy
            card = self.enemy.hand.pop(card_index)

        # Calculate starting position based on owner
        card_width = 150
        card_height = 200
        gap = 20

        if owner == "player":
            # Calculate card position in player's hand
            hand_size = 5
            total_width = (card_width * hand_size) + (gap * (hand_size - 1))
            start_x = (self.screen.get_width() - total_width) // 2
            card_y = self.screen.get_height() - card_height - 30
            card_x = start_x + (card_index * (card_width + gap))
            start_pos = (card_x, card_y)
        else:  # enemy
            # Start from enemy deck position at top of screen
            hand_size = 5
            total_width = (card_width * hand_size) + (gap * (hand_size - 1))
            player_hand_start_x = (self.screen.get_width() - total_width) // 2
            enemy_deck_x = player_hand_start_x - card_width - gap
            enemy_deck_y = 30
            start_pos = (enemy_deck_x, enemy_deck_y)

        # Staging area position (center of screen)
        staging_x = (self.screen.get_width() - card_width) // 2
        staging_y = (self.screen.get_height() - card_height) // 2
        end_pos = (staging_x, staging_y)

        # Create animation (0.2 seconds for fast movement)
        animation = CardAnimation(card, card_index, start_pos, end_pos, 0.2)
        self.active_animations.append(animation)

        # Store the card as staged
        self.staged_card = card
        self.staged_card_index = card_index
        self.staged_card_owner = owner

        # Set animation state
        if owner == "player":
            self.state = CombatState.PLAYER_CARD_ANIMATING
        else:
            self.state = CombatState.ENEMY_CARD_ANIMATING

    def _cancel_staged_card(self) -> None:
        """
        Cancel the staged card and return it to the owner's hand.
        """
        if not self.staged_card:
            return

        # Determine end position (original hand position)
        layout = self._get_card_layout()
        card_width = layout['card_width']
        gap = layout['gap']
        
        # Calculate x position based on the original index
        # Note: We use the same formula as _render_player_hand
        end_x = layout['start_x'] + (self.staged_card_index * (card_width + gap))
        end_y = layout['card_y']
        end_pos = (end_x, end_y)

        # Start position is the staging area
        staging_x = (self.screen.get_width() - card_width) // 2
        staging_y = (self.screen.get_height() - layout['card_height']) // 2
        start_pos = (staging_x, staging_y)

        # Create return animation
        animation = CardAnimation(self.staged_card, self.staged_card_index, start_pos, end_pos, 0.2)
        self.active_animations.append(animation)

        # Track the card being returned (for reinsertion after animation)
        self.returning_card = self.staged_card
        self.returning_card_index = self.staged_card_index

        # Clear staging state - card will be reinserted when animation completes
        self.staged_card = None
        self.staged_card_index = None
        self.staged_card_owner = None
        self.state = CombatState.PLAYER_CARD_ANIMATING

    def _start_enemy_discard_animation(self, card_index: int) -> None:
        """
        Start animation for an enemy discarding a card (useless move).
        """
        card = self.enemy.hand.pop(card_index)
        
        # Start pos: Enemy hand area (top centerish)
        start_pos = (self.screen.get_width() // 2, 30)
        
        # End pos: Enemy discard pile area (left side)
        end_pos = (50, self.screen.get_height() // 2 - 20)
        
        # Create animation
        animation = CardAnimation(card, card_index, start_pos, end_pos, 0.5)
        self.active_animations.append(animation)
        
        # Track this specifically as a discard action, not a play
        self.enemy_discarding_card = card
        self.state = CombatState.ENEMY_DISCARD_ANIMATING

        # We do NOT set self.staged_card, because we don't want to trigger _resolve_staged_card

    def _start_enemy_turn(self) -> None:
        """Start the enemy's turn with a thinking delay."""
        self.state = CombatState.ENEMY_THINKING
        self.enemy_think_timer = 0.0

    def _start_reshuffle(self, target: str, owner: str) -> None:
        """Start the deck reshuffle process with a visual delay.

        Args:
            target: "player" or "enemy" - who is reshuffling their deck
            owner: "player" or "enemy" - whose turn just ended
        """
        self.state = CombatState.RESHUFFLING
        self.reshuffle_timer = 0.0
        self.reshuffle_target = target
        self.reshuffle_owner = owner

    def _execute_reshuffle(self) -> None:
        """Execute the actual deck reshuffle and continue turn progression."""
        if self.reshuffle_target == "player":
            # Move discard pile to deck
            self.player.deck = self.player.discard_pile.copy()
            self.player.discard_pile.clear()
            # Shuffle the new deck
            self.player.shuffle_deck()
        elif self.reshuffle_target == "enemy":
            # Move discard pile to deck
            self.enemy.deck = self.enemy.discard_pile.copy()
            self.enemy.discard_pile.clear()
            # Shuffle the new deck
            self.enemy.shuffle_deck()

        # Store owner for turn progression
        owner = self.reshuffle_owner

        # Clear reshuffle data
        self.reshuffle_target = None
        self.reshuffle_owner = None

        # Continue turn progression (only if combat is still active)
        if self.state not in (CombatState.VICTORY, CombatState.DEFEAT):
            if owner == "player":
                # Player's turn just ended, start enemy turn
                self._start_enemy_turn()
            else:
                # Enemy's turn just ended, back to player turn
                self.enemy.draw_card()
                self.turn += 1
                self.state = CombatState.PLAYER_TURN

    def _start_discard_select(self) -> None:
        """Start the discard selection process."""
        self.state = CombatState.PLAYER_DISCARDING

    def _execute_enemy_action(self) -> None:
        """Execute the enemy's action (play a card)."""

        if not self.enemy.hand:
            self.state = CombatState.PLAYER_TURN
            return

        # 1. Calculate utility for all cards
        best_card_index = -1
        best_score = -1.0
        
        for i, card in enumerate(self.enemy.hand):
            score = self._calculate_utility(card, self.enemy, self.player)
            if score > best_score:
                best_score = score
                best_card_index = i
        
        # 2. Decide: Play or Discard?
        # If the best move is positive, play it.
        if best_score > 0:
            self._start_card_animation(best_card_index, owner="enemy")
        else:
            # No good moves. Discard the first card to cycle the deck.
            # (In a more advanced version, we'd discard the lowest utility card)
            self._start_enemy_discard_animation(0)

    def _calculate_utility(self, card: Card, owner: Player, opponent: Player) -> float:
        """
        Calculate the utility score of a card based on context and persona.
        Returns a float score (higher is better). Score <= 0 means 'do not play'.
        """
        score = 0.0
        
        if card.card_type == CardType.ATTACK:
            score = float(getattr(card, 'damage', 0))
            
            # Persona modifiers
            if self.ai_persona == "aggressive":
                score *= 1.5
            elif self.ai_persona == "timid":
                score *= 0.8
                
            # Context: Lethal blow (Finish them!)
            if opponent.hit_points <= card.damage:
                score += 100.0
                
        elif card.card_type == CardType.HEAL:
            heal_amt = getattr(card, 'heal_amount', 0)
            hp_percent = owner.hit_points / owner.max_hit_points
            
            if hp_percent >= 1.0:
                score = 0.0 # Useless at full health
            elif hp_percent < 0.3:
                score = heal_amt * 3.0 # Critical health - panic heal
            elif hp_percent < 0.7:
                score = heal_amt * 1.5 # Hurt - good to heal
            else:
                score = heal_amt * 0.5 # Lightly hurt - low priority
                
            # Persona modifiers
            if self.ai_persona == "timid":
                score *= 1.5
            elif self.ai_persona == "aggressive":
                score *= 0.8

        return score

    def _should_open_counter_window(self) -> bool:
        """Check if player should get a chance to counter the staged card."""
        if not self.staged_card:
            return False
        # Only counter enemy attacks
        if self.staged_card_owner != "enemy":
            return False
        if self.staged_card.card_type != CardType.ATTACK:
            return False
        # Check if player has any defense cards
        return any(c.card_type == CardType.DEFENSE for c in self.player.hand)

    def _resolve_staged_card(self) -> None:
        """Execute the staged card's effect and move it to discard."""
        if self.staged_card:
            # Store owner before clearing (we need it for turn progression)
            owner = self.staged_card_owner

            # Determine target and discard pile based on who played the card
            if owner == "player":
                source = self.player
                target = self.enemy
                discard_pile = self.player.discard_pile
            else:  # enemy
                source = self.enemy
                target = self.player
                discard_pile = self.enemy.discard_pile

            # Apply counter if one was played
            if self.counter_card and self.staged_card.card_type == CardType.ATTACK:
                # Reduce damage by defense value
                original_damage = self.staged_card.damage
                reduced_damage = max(0, original_damage - self.counter_card.defense_value)
                # Temporarily modify damage for this resolution
                self.staged_card.damage = reduced_damage
                self.staged_card.play(source, target)
                self.staged_card.damage = original_damage  # Restore original damage
                # Discard the counter card
                self.player.discard_pile.append(self.counter_card)
                self.counter_card = None
                self.counter_card_index = None
            else:
                # Normal resolution
                self.staged_card.play(source, target)

            discard_pile.append(self.staged_card)

            # Check for victory/defeat/last stand
            self._check_vital_signs()

            if self.state in (CombatState.VICTORY, CombatState.DEFEAT):
                return

            # Clear staging area
            self.staged_card = None
            self.staged_card_index = None
            self.staged_card_owner = None

            # Check for empty hand and deck. If so, reshuffle the discard pile
            # Check player's deck
            if len(self.player.hand) == 0 and len(self.player.deck) == 0 and len(self.player.discard_pile) > 0:
                self._start_reshuffle("player", owner)
                return  # Exit early, reshuffle will continue the flow

            # Check enemy's deck
            if len(self.enemy.hand) == 0 and len(self.enemy.deck) == 0 and len(self.enemy.discard_pile) > 0:
                self._start_reshuffle("enemy", owner)
                return  # Exit early, reshuffle will continue the flow

            # Handle turn progression
            if not self.last_stand_active:
                if owner == "player":
                    # Player's turn just ended, start enemy turn
                    self._start_enemy_turn()
                else:
                    # Enemy's turn just ended, back to player turn
                    # Enemy draws until hand is full (5 cards)
                    while len(self.enemy.hand) < 5:
                        if not self.enemy.draw_card():
                            break  # Deck is empty
                    # Increment turn counter
                    self.turn += 1
                    self.state = CombatState.PLAYER_TURN

    def _check_vital_signs(self) -> None:
        """Check if any player is defeated or entering Last Stand."""
        # Check Enemy
        if self.enemy.is_defeated():
            self.state = CombatState.VICTORY
            self._handle_combat_completion("victory")
            return

        # Check Player
        if self.player.is_defeated():
            # Check for heals in hand
            has_heals = any(
                hasattr(card, 'card_type') and card.card_type.value == 'heal'
                for card in self.player.hand
            )

            if has_heals:
                self.last_stand_active = True
            else:
                self.state = CombatState.DEFEAT
                self._handle_combat_completion("defeat")
        else:
            # Player is alive. If they were in last stand, they are safe now.
            if self.last_stand_active:
                self.last_stand_active = False

    def _handle_combat_completion(self, result: str) -> None:
        """
        Handle combat completion.

        Args:
            result: Combat result ("victory" or "defeat")
        """

        # Update game context
        self.game_context.battle_attempts[self.battle_id] = self.game_context.battle_attempts.get(self.battle_id, 0) + 1
        if result == "victory":
            self.game_context.completed_battles.append(self.battle_id)

    def _debug_auto_win(self) -> None:
        """Debug method to instantly win the combat."""
        self.enemy.hit_points = 0
        self.state = CombatState.VICTORY
        self._handle_combat_completion("victory")

    def _debug_auto_lose(self) -> None:
        """Debug method to instantly lose the combat."""
        self.player.hit_points = 0
        self.state = CombatState.DEFEAT
        self._handle_combat_completion("defeat")

    def _after_combat(self) -> None:
        # For demo, just reset combat to play again. In a full game, this would transition to rewards or next battle.
        self._reset_combat()
        return None

    def _reset_combat(self) -> None:
        """Reset combat state for a new round."""
        # Reset player deck
        self.player.reset_deck()
        self.player.shuffle_deck()

        # Reset enemy deck
        self.enemy.reset_deck()
        self.enemy.shuffle_deck()

        # Give enemy a fresh hand
        for _ in range(5):
            self.enemy.draw_card()

        # Reset both players' HP
        self.player.hit_points = self.player.max_hit_points
        self.enemy.hit_points = self.enemy.max_hit_points

        # Reset state machine
        self.state = CombatState.PLAYER_TURN
        self.turn = 1
        self.round += 1
        self.last_stand_active = False

        # Clear animations and staging
        self.active_animations.clear()
        self.staged_card = None
        self.staged_card_index = None
        self.staged_card_owner = None
        self.returning_card = None
        self.returning_card_index = None

        # Reset timers
        self.enemy_think_timer = 0.0
        self.enemy_discarding_card = None
        self.reshuffle_timer = 0.0
        self.reshuffle_target = None
        self.reshuffle_owner = None

        # Reset counter state
        self.counter_card = None
        self.counter_card_index = None
        self.skip_counter_hovered = False

    def update(self, dt: float) -> None:
        """
        Update card combat logic.

        Args:
            dt: Delta time in seconds
        """
        match self.state:
            case CombatState.ENEMY_THINKING:
                self.enemy_think_timer += dt
                if self.enemy_think_timer >= self.enemy_think_duration:
                    self._execute_enemy_action()

            case CombatState.RESHUFFLING:
                self.reshuffle_timer += dt
                if self.reshuffle_timer >= self.reshuffle_duration:
                    self._execute_reshuffle()

            case CombatState.PLAYER_CARD_ANIMATING | CombatState.ENEMY_CARD_ANIMATING | CombatState.ENEMY_DISCARD_ANIMATING | CombatState.COUNTER_ANIMATING:
                self._update_animations(dt)

            case _:
                # Other states don't need update logic
                pass

    def _update_animations(self, dt: float) -> None:
        """Update active animations and handle completion transitions."""
        for animation in self.active_animations[:]:
            if animation.update(dt):
                self.active_animations.remove(animation)

                # All animations complete - determine next state
                if not self.active_animations:
                    match self.state:
                        case CombatState.PLAYER_CARD_ANIMATING:
                            # Check if this was a return animation or a play animation
                            if self.returning_card:
                                # Reinsert card into hand
                                self.player.hand.insert(self.returning_card_index, self.returning_card)
                                self.returning_card = None
                                self.returning_card_index = None
                                self.state = CombatState.PLAYER_TURN
                            else:
                                # Normal play - go to resolve
                                self.state = CombatState.WAITING_FOR_RESOLVE

                        case CombatState.ENEMY_CARD_ANIMATING:
                            if self._should_open_counter_window():
                                self.state = CombatState.WAITING_FOR_COUNTER
                            else:
                                self.state = CombatState.WAITING_FOR_RESOLVE

                        case CombatState.ENEMY_DISCARD_ANIMATING:
                            self.enemy.discard_pile.append(self.enemy_discarding_card)
                            self.enemy_discarding_card = None
                            self.enemy.draw_card()
                            self.turn += 1
                            self.state = CombatState.PLAYER_TURN

                        case CombatState.COUNTER_ANIMATING:
                            self.state = CombatState.RESOLVE_WITH_COUNTER

    # =========================================================================
    # RENDER HELPER METHODS
    # =========================================================================

    def _can_player_act(self) -> bool:
        """Check if the player can currently take actions."""
        return self.state == CombatState.PLAYER_TURN

    def _get_card_layout(self) -> dict:
        """Get common card layout dimensions used across render methods."""
        hand_size = 5
        card_width = 150
        card_height = 200
        gap = 20

        total_width = (card_width * hand_size) + (gap * (hand_size - 1))
        start_x = (self.screen.get_width() - total_width) // 2
        card_y = self.screen.get_height() - card_height - 30

        return {
            'hand_size': hand_size,
            'card_width': card_width,
            'card_height': card_height,
            'gap': gap,
            'hover_lift': 30,
            'total_width': total_width,
            'start_x': start_x,
            'card_y': card_y,
        }

    def _get_skip_counter_button_rect(self, layout: dict) -> pygame.Rect:
        """Get the rectangle for the Skip Counter button."""
        button_width = 150
        button_height = 50
        # Position to the right of the staged card (same as resolve button area)
        staging_x = (self.screen.get_width() - layout['card_width']) // 2
        staging_y = (self.screen.get_height() - layout['card_height']) // 2
        button_x = staging_x + layout['card_width'] + 40
        button_y = staging_y + layout['card_height'] // 2 - button_height // 2
        return pygame.Rect(button_x, button_y, button_width, button_height)

    def _render_hud(self) -> None:
        """Render the heads-up display (title, instructions, turn/round counters)."""
        # Title
        title_surface = self.font.render("Card Combat", True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(self.screen.get_width() // 2, 100))
        self.screen.blit(title_surface, title_rect)

        # Instructions
        instructions_surface = self.font.render("(ESC for menu)", True, (200, 200, 200))
        instructions_rect = instructions_surface.get_rect(center=(self.screen.get_width() // 2, 200))
        self.screen.blit(instructions_surface, instructions_rect)

        # Turn and Round counters (top right)
        counter_height = 50
        counter_gap = 50

        turn_text = f"Turn: {self.turn}"
        turn_surface = self.font.render(turn_text, True, (255, 255, 100))
        turn_rect = turn_surface.get_rect(topright=(self.screen.get_width() - 50, counter_height))
        self.screen.blit(turn_surface, turn_rect)

        round_text = f"Round: {self.round}"
        round_surface = self.font.render(round_text, True, (255, 255, 100))
        round_rect = round_surface.get_rect(topright=(self.screen.get_width() - 50, counter_height + counter_gap))
        self.screen.blit(round_surface, round_rect)

    def _render_hp_displays(self) -> None:
        """Render player and opponent HP displays."""
        hp_x = 50
        hp_y_start = self.screen.get_height() // 2 - 100

        # Opponent HP
        opponent_name_surface = self.font.render(self.enemy.name, True, (255, 100, 100))
        self.screen.blit(opponent_name_surface, (hp_x, hp_y_start))

        opponent_hp_text = f"HP: {self.enemy.hit_points}/{self.enemy.max_hit_points}"
        opponent_hp_surface = self.card_font.render(opponent_hp_text, True, (255, 255, 255))
        self.screen.blit(opponent_hp_surface, (hp_x, hp_y_start + 50))

        opponent_discard_text = f"Discard pile: {len(self.enemy.discard_pile)} cards"
        opponent_discard_surface = self.card_font.render(opponent_discard_text, True, (255, 255, 255))
        self.screen.blit(opponent_discard_surface, (hp_x, hp_y_start + 80))

        # Player HP
        player_name_surface = self.font.render(self.player.name, True, (100, 200, 255))
        self.screen.blit(player_name_surface, (hp_x, hp_y_start + 120))

        player_hp_text = f"HP: {self.player.hit_points}/{self.player.max_hit_points}"
        player_hp_surface = self.card_font.render(player_hp_text, True, (255, 255, 255))
        self.screen.blit(player_hp_surface, (hp_x, hp_y_start + 170))

        player_discard_text = f"Discard pile: {len(self.player.discard_pile)} cards"
        player_discard_surface = self.card_font.render(player_discard_text, True, (255, 255, 255))
        self.screen.blit(player_discard_surface, (hp_x, hp_y_start + 200))

    def _render_deck(self, x: int, y: int, layout: dict, label: str, card_count: int,
                     bg_color: Tuple[int, int, int], border_color: Tuple[int, int, int]) -> None:
        """Render a deck card (player or enemy).

        Args:
            x: X position of deck
            y: Y position of deck
            layout: Card layout dimensions
            label: Label text for the deck
            card_count: Number of cards in deck
            bg_color: Background color
            border_color: Border color
        """
        card_width = layout['card_width']
        card_height = layout['card_height']

        deck_rect = pygame.Rect(x, y, card_width, card_height)
        pygame.draw.rect(self.screen, bg_color, deck_rect)
        pygame.draw.rect(self.screen, border_color, deck_rect, 2)

        # Deck label
        deck_label = self.font.render(label, True, (255, 255, 255))
        deck_label_rect = deck_label.get_rect(center=(x + card_width // 2, y + 60))
        self.screen.blit(deck_label, deck_label_rect)

        # Card count
        x_loc = x + card_width // 2
        deck_size = "Unknown"
        if label == "Deck":
            deck_size = str(self.player_deck_size)
            count_text = f"{card_count} cards"
            count_text_2 = f"{deck_size} max"
        elif label == "Enemy":
            deck_size = str(self.enemy_deck_size)
            count_text = f"Hand: {card_count}"
            count_text_2 = f"Deck: {len(self.enemy.deck)} of {deck_size}"
            x_loc = x + card_width // 3

        count_surface = self.card_font.render(count_text, True, (255, 255, 255))
        count_rect = count_surface.get_rect(center=(x_loc, y + card_height // 2 + 20))
        count_surface_2 = self.card_font.render(count_text_2, True, (255, 255, 255))
        count_rect_2 = count_surface.get_rect(center=(x_loc, y + card_height // 2 + 40))
        self.screen.blit(count_surface, count_rect)
        self.screen.blit(count_surface_2, count_rect_2)

    def _render_decks(self, layout: dict) -> None:
        """Render both player and enemy decks."""
        deck_x = layout['start_x'] - layout['card_width'] - layout['gap']

        # Player deck (bottom)
        self._render_deck(
            deck_x, layout['card_y'], layout,
            "Deck", len(self.player.deck),
            (100, 50, 150), (200, 150, 255)
        )

        # Enemy deck (top)
        self._render_deck(
            deck_x, 30, layout,
            "Enemy", len(self.enemy.hand),
            (150, 50, 50), (255, 100, 100)
        )

    def _render_card(self, card: Card, x: int, y: int, layout: dict,
                     highlighted: bool = False,
                     border_color: Optional[Tuple[int, int, int]] = None) -> None:
        """Render a single card at the specified position.

        Args:
            card: The card to render
            x: X position
            y: Y position
            layout: Card layout dimensions
            highlighted: Whether the card is highlighted/hovered
            border_color: Optional override for border color
        """
        card_width = layout['card_width']
        card_height = layout['card_height']

        # Determine colors
        bg_color = (70, 140, 70) if highlighted else (50, 100, 50)
        if border_color is None:
            border_color = (255, 255, 100) if highlighted else (255, 255, 255)
        border_width = 3 if highlighted else 2

        card_rect = pygame.Rect(x, y, card_width, card_height)
        pygame.draw.rect(self.screen, bg_color, card_rect)
        pygame.draw.rect(self.screen, border_color, card_rect, border_width)

        # Card name
        name_surface = self.card_font.render(card.name, True, (255, 255, 255))
        name_rect = name_surface.get_rect(center=(x + card_width // 2, y + 30))
        self.screen.blit(name_surface, name_rect)

        # Damage (if applicable)
        if hasattr(card, 'damage'):
            damage_surface = self.font.render(str(card.damage), True, (255, 200, 0))
            damage_rect = damage_surface.get_rect(center=(x + card_width // 2, y + card_height // 2))
            self.screen.blit(damage_surface, damage_rect)

        # Description
        desc_surface = self.card_font.render(card.description, True, (200, 200, 200))
        desc_rect = desc_surface.get_rect(center=(x + card_width // 2, y + card_height - 30))
        self.screen.blit(desc_surface, desc_rect)

    def _render_empty_card_slot(self, x: int, y: int, layout: dict) -> None:
        """Render an empty card slot.

        Args:
            x: X position
            y: Y position
            layout: Card layout dimensions
        """
        card_width = layout['card_width']
        card_height = layout['card_height']

        empty_rect = pygame.Rect(x, y, card_width, card_height)
        pygame.draw.rect(self.screen, (30, 30, 30), empty_rect)
        pygame.draw.rect(self.screen, (100, 100, 100), empty_rect, 2)

        empty_surface = self.card_font.render("empty", True, (100, 100, 100))
        empty_text_rect = empty_surface.get_rect(center=(x + card_width // 2, y + card_height // 2))
        self.screen.blit(empty_surface, empty_text_rect)

    def _render_player_hand(self, mouse_pos: Tuple[int, int], player_can_act: bool, layout: dict) -> None:
        """Render the player's hand of cards.

        Args:
            mouse_pos: Current mouse position
            player_can_act: Whether player can currently take actions
            layout: Card layout dimensions
        """
        # Reset hovered card tracking
        self.hovered_card_index = None

        # Allow interaction during player turn OR discard selection
        can_interact = player_can_act or self.state == CombatState.PLAYER_DISCARDING

        # Check if player has a card staged or returning (need to show gap in hand)
        gap_index = None
        if self.staged_card is not None and self.staged_card_owner == "player" and self.staged_card_index is not None:
            gap_index = self.staged_card_index
        elif self.returning_card is not None and self.returning_card_index is not None:
            gap_index = self.returning_card_index

        for visual_slot in range(layout['hand_size']):
            card_x = layout['start_x'] + (visual_slot * (layout['card_width'] + layout['gap']))

            # Determine actual hand index, accounting for gap
            if gap_index is not None:
                if visual_slot == gap_index:
                    # This is where the staged/returning card was - render empty slot
                    self._render_empty_card_slot(card_x, layout['card_y'], layout)
                    continue
                elif visual_slot < gap_index:
                    actual_index = visual_slot
                else:
                    # After the gap, shift index down by 1
                    actual_index = visual_slot - 1
            else:
                actual_index = visual_slot

            # Check if we have a card at this actual index
            if actual_index >= len(self.player.hand):
                self._render_empty_card_slot(card_x, layout['card_y'], layout)
                continue

            card = self.player.hand[actual_index]

            # Skip defense cards during counter prompt (they're rendered separately)
            if self.state == CombatState.WAITING_FOR_COUNTER and card.card_type == CardType.DEFENSE:
                continue

            # Check hover state
            base_card_rect = pygame.Rect(card_x, layout['card_y'], layout['card_width'], layout['card_height'])
            is_hovering = base_card_rect.collidepoint(mouse_pos) and can_interact

            # In Last Stand, only allow hovering Heal cards
            if self.last_stand_active:
                if not (hasattr(card, 'card_type') and card.card_type.value == 'heal'):
                    is_hovering = False

            # Update hovered card index if hovering
            if is_hovering:
                self.hovered_card_index = actual_index

            # Also hover if selected for discard
            if self.discard_cards_hovered.get(actual_index, False):
                is_hovering = True

            # Calculate y position with hover lift
            current_card_y = layout['card_y'] - layout['hover_lift'] if is_hovering else layout['card_y']

            self._render_card(card, card_x, current_card_y, layout, highlighted=is_hovering)

    def _get_button_text(self, default_text: str) -> str:
        """Get button text based on current game state.

        Args:
            default_text: The default text to show when player can act

        Returns:
            Appropriate button text for current state
        """
        match self.state:
            case CombatState.ENEMY_THINKING | CombatState.ENEMY_CARD_ANIMATING | CombatState.ENEMY_DISCARD_ANIMATING:
                return "Enemy Turn"
            case CombatState.VICTORY | CombatState.DEFEAT:
                return "Combat Over"
            case CombatState.PLAYER_DISCARDING:
                return "Discarding"
            case _:
                return default_text

    def _render_action_button(self, x: int, y: int, width: int, height: int,
                              text: str, enabled: bool, mouse_pos: Tuple[int, int],
                              normal_color: Tuple[int, int, int],
                              hover_color: Tuple[int, int, int]) -> bool:
        """Render an action button and return whether it's being hovered.

        Args:
            x: X position
            y: Y position
            width: Button width
            height: Button height
            text: Button text
            enabled: Whether button is enabled
            mouse_pos: Current mouse position
            normal_color: Color when not hovered
            hover_color: Color when hovered

        Returns:
            True if button is being hovered and enabled
        """
        button_rect = pygame.Rect(x, y, width, height)
        is_hovering = button_rect.collidepoint(mouse_pos) and enabled

        # Determine color
        if not enabled:
            color = (80, 80, 80)  # Gray when disabled
        elif is_hovering:
            color = hover_color
        else:
            color = normal_color

        pygame.draw.rect(self.screen, color, button_rect)
        pygame.draw.rect(self.screen, (255, 255, 255), button_rect, 2)

        text_surface = self.card_font.render(text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(x + width // 2, y + height // 2))
        self.screen.blit(text_surface, text_rect)

        return is_hovering

    def _render_action_buttons(self, mouse_pos: Tuple[int, int], player_can_act: bool, layout: dict) -> None:
        """Render the action buttons (Draw, Pass, Discard).

        Args:
            mouse_pos: Current mouse position
            player_can_act: Whether player can currently take actions
            layout: Card layout dimensions
        """
        button_width = layout['card_width']
        button_height = 50
        button_gap = 10
        button_x = layout['start_x'] + (5 * (layout['card_width'] + layout['gap']))

        hand_is_full = len(self.player.hand) >= layout['hand_size']

        # Draw button - also enabled during counter window for draw-to-fill
        draw_y = layout['card_y']
        counter_draw_enabled = self.state == CombatState.WAITING_FOR_COUNTER and not hand_is_full
        draw_enabled = (player_can_act and not hand_is_full and not self.last_stand_active) or counter_draw_enabled
        draw_text = "Hand Full" if hand_is_full else self._get_button_text("Draw Card")
        self.draw_button_hovered = self._render_action_button(
            button_x, draw_y, button_width, button_height,
            draw_text, draw_enabled, mouse_pos,
            (50, 150, 50), (100, 200, 100)
        )

        # Pass button
        pass_y = draw_y + button_height + button_gap
        pass_enabled = player_can_act  # Always enabled when player can act (Pass or Give Up)
        pass_text = "Give Up" if self.last_stand_active else self._get_button_text("Pass Turn")
        self.pass_button_hovered = self._render_action_button(
            button_x, pass_y, button_width, button_height,
            pass_text, pass_enabled, mouse_pos,
            (50, 100, 150), (100, 150, 200)
        )

        # Discard button
        discard_y = pass_y + button_height + button_gap
        discard_enabled = player_can_act and not self.last_stand_active
        self.discard_button_hovered = self._render_action_button(
            button_x, discard_y, button_width, button_height,
            self._get_button_text("Discard"), discard_enabled, mouse_pos,
            (150, 0, 0), (200, 0, 0)
        )

    def _render_animating_cards(self, layout: dict) -> None:
        """Render cards that are currently animating.

        Args:
            layout: Card layout dimensions
        """
        for animation in self.active_animations:
            pos = animation.get_current_pos()
            self._render_card(animation.card, pos[0], pos[1], layout)

    def _render_staged_card(self, layout: dict) -> None:
        """Render the staged card waiting for resolution.

        Args:
            layout: Card layout dimensions
        """
        if self.state not in (CombatState.WAITING_FOR_RESOLVE, CombatState.RESOLVE_WITH_COUNTER):
            return
        if not self.staged_card:
            return

        card_width = layout['card_width']
        card_height = layout['card_height']

        staging_x = (self.screen.get_width() - card_width) // 2
        staging_y = (self.screen.get_height() - card_height) // 2

        # Determine border color based on owner
        if self.staged_card_owner == "player":
            border_color = (255, 255, 100)  # Yellow for player
        else:
            border_color = (255, 100, 100)  # Red for enemy

        self._render_card(self.staged_card, staging_x, staging_y, layout,
                         highlighted=True, border_color=border_color)

        # If there's a counter card, render it too
        if self.state == CombatState.RESOLVE_WITH_COUNTER and self.counter_card:
            counter_x = staging_x - card_width - 20
            self._render_card(self.counter_card, counter_x, staging_y, layout,
                             highlighted=True, border_color=(0, 200, 200))

        # Render "CLICK TO RESOLVE" indicator
        self._render_resolve_indicator(staging_x + card_width + 40, staging_y + card_height // 2)

    def _render_resolve_indicator(self, x: int, y: int) -> None:
        """Render the 'Click to Resolve' indicator box.

        Args:
            x: X position of the indicator
            y: Y center position of the indicator
        """
        # Draw arrow
        arrow_text = "←"
        arrow_surface = self.font.render(arrow_text, True, (255, 255, 100))
        arrow_rect = arrow_surface.get_rect(midleft=(x - 30, y))
        self.screen.blit(arrow_surface, arrow_rect)

        # Determine colors based on owner
        if self.staged_card_owner == "player":
            box_color = (100, 100, 0)
            box_border_color = (255, 255, 0)
            text_color = (255, 255, 100)
        else:
            box_color = (100, 0, 0)
            box_border_color = (255, 0, 0)
            text_color = (255, 100, 100)

        # Draw resolve box
        box_width = 200
        box_height = 80
        box_rect = pygame.Rect(x, y - box_height // 2, box_width, box_height)
        pygame.draw.rect(self.screen, box_color, box_rect)
        pygame.draw.rect(self.screen, box_border_color, box_rect, 3)

        # Draw text
        click_surface = self.card_font.render("CLICK TO", True, (255, 255, 255))
        click_rect = click_surface.get_rect(center=(x + box_width // 2, y - 15))
        self.screen.blit(click_surface, click_rect)

        resolve_surface = self.card_font.render("RESOLVE", True, text_color)
        resolve_rect = resolve_surface.get_rect(center=(x + box_width // 2, y + 15))
        self.screen.blit(resolve_surface, resolve_rect)

    def _render_discard_modal(self, mouse_pos: Tuple[int, int]) -> None:
        """Render the discard selection modal.

        Args:
            mouse_pos: Current mouse position
        """
        if self.state != CombatState.PLAYER_DISCARDING:
            return

        modal_width = 400
        modal_height = 130
        modal_x = (self.screen.get_width() - modal_width) // 2
        modal_y = (self.screen.get_height() - modal_height) // 2

        # Modal background
        modal_rect = pygame.Rect(modal_x, modal_y, modal_width, modal_height)
        pygame.draw.rect(self.screen, (50, 50, 50), modal_rect)
        pygame.draw.rect(self.screen, (255, 255, 255), modal_rect, 4)

        # Button dimensions
        button_width = 300
        button_height = 50
        button_x = modal_x + (modal_width - button_width) // 2
        button_gap = 10
        padding = 10

        # Confirm button
        confirm_y = modal_y + padding
        confirm_rect = pygame.Rect(button_x, confirm_y, button_width, button_height)
        self.discard_confirm_hover = confirm_rect.collidepoint(mouse_pos)

        confirm_color = (100, 150, 100) if self.discard_confirm_hover else (50, 100, 50)
        pygame.draw.rect(self.screen, confirm_color, confirm_rect)
        pygame.draw.rect(self.screen, (255, 255, 255), confirm_rect, 2)

        confirm_surface = self.font.render("Confirm", True, (255, 255, 255))
        confirm_text_rect = confirm_surface.get_rect(center=confirm_rect.center)
        self.screen.blit(confirm_surface, confirm_text_rect)

        # Cancel button
        cancel_y = confirm_y + button_height + button_gap
        cancel_rect = pygame.Rect(button_x, cancel_y, button_width, button_height)
        self.discard_cancel_hover = cancel_rect.collidepoint(mouse_pos)

        cancel_color = (150, 100, 100) if self.discard_cancel_hover else (100, 50, 50)
        pygame.draw.rect(self.screen, cancel_color, cancel_rect)
        pygame.draw.rect(self.screen, (255, 255, 255), cancel_rect, 2)

        cancel_surface = self.font.render("Cancel", True, (255, 255, 255))
        cancel_text_rect = cancel_surface.get_rect(center=cancel_rect.center)
        self.screen.blit(cancel_surface, cancel_text_rect)

    def _render_counter_prompt(self, mouse_pos: Tuple[int, int], layout: dict) -> None:
        """Render the counter prompt when player can respond to an attack."""
        if self.state != CombatState.WAITING_FOR_COUNTER:
            return

        # Render the staged attack card (same position as normal staged card)
        card_width = layout['card_width']
        card_height = layout['card_height']
        staging_x = (self.screen.get_width() - card_width) // 2
        staging_y = (self.screen.get_height() - card_height) // 2

        # Draw the attack card with red border (enemy's card)
        self._render_card(self.staged_card, staging_x, staging_y, layout,
                         highlighted=True, border_color=(255, 100, 100))

        # Draw "COUNTER?" prompt above the card
        prompt_font = pygame.font.Font(None, 56)
        prompt_surface = prompt_font.render("COUNTER?", True, (255, 255, 100))
        prompt_rect = prompt_surface.get_rect(center=(self.screen.get_width() // 2, staging_y - 40))
        self.screen.blit(prompt_surface, prompt_rect)

        # Draw damage indicator
        if hasattr(self.staged_card, 'damage'):
            damage_text = f"Incoming: {self.staged_card.damage} damage"
            damage_surface = self.card_font.render(damage_text, True, (255, 150, 150))
            damage_rect = damage_surface.get_rect(center=(self.screen.get_width() // 2, staging_y - 10))
            self.screen.blit(damage_surface, damage_rect)

        # Draw Skip button
        skip_rect = self._get_skip_counter_button_rect(layout)
        self.skip_counter_hovered = skip_rect.collidepoint(mouse_pos)
        skip_color = (150, 100, 100) if self.skip_counter_hovered else (100, 50, 50)
        pygame.draw.rect(self.screen, skip_color, skip_rect)
        pygame.draw.rect(self.screen, (255, 255, 255), skip_rect, 2)

        skip_surface = self.card_font.render("Skip", True, (255, 255, 255))
        skip_text_rect = skip_surface.get_rect(center=skip_rect.center)
        self.screen.blit(skip_surface, skip_text_rect)

        # Highlight defense cards in hand with special border
        for i, card in enumerate(self.player.hand):
            if card.card_type == CardType.DEFENSE:
                card_x = layout['start_x'] + (i * (card_width + layout['gap']))
                # Lift defense cards to show they're selectable
                card_y = layout['card_y'] - layout['hover_lift']

                # Check if this defense card is hovered
                card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
                is_hovered = card_rect.collidepoint(mouse_pos)

                # Draw with cyan/blue highlight for defense cards
                border_color = (100, 255, 255) if is_hovered else (0, 200, 200)
                self._render_card(card, card_x, card_y, layout,
                                highlighted=is_hovered, border_color=border_color)

        # Draw instruction text
        instruction_text = "Click a DEFENSE card to counter, or Skip"
        instruction_surface = self.card_font.render(instruction_text, True, (200, 200, 200))
        instruction_rect = instruction_surface.get_rect(center=(self.screen.get_width() // 2,
                                                                layout['card_y'] - layout['hover_lift'] - 20))
        self.screen.blit(instruction_surface, instruction_rect)

    def _render_enemy_thinking_overlay(self) -> None:
        """Render the 'Enemy Thinking' overlay."""
        if self.state != CombatState.ENEMY_THINKING:
            return

        box_width = 300
        box_height = 100
        box_x = (self.screen.get_width() - box_width) // 2
        box_y = (self.screen.get_height() - box_height) // 2

        box_rect = pygame.Rect(box_x, box_y, box_width, box_height)
        pygame.draw.rect(self.screen, (100, 0, 0), box_rect)
        pygame.draw.rect(self.screen, (255, 100, 100), box_rect, 4)

        think_surface = self.font.render("ENEMY THINKING...", True, (255, 255, 255))
        think_rect = think_surface.get_rect(center=(box_x + box_width // 2, box_y + box_height // 2))
        self.screen.blit(think_surface, think_rect)

    def _render_reshuffle_overlay(self) -> None:
        """Render the 'Reshuffling Deck' overlay."""
        if self.state != CombatState.RESHUFFLING:
            return

        box_width = 400
        box_height = 120
        box_x = (self.screen.get_width() - box_width) // 2
        box_y = (self.screen.get_height() - box_height) // 2

        # Color based on who is reshuffling
        if self.reshuffle_target == "player":
            box_color = (50, 50, 150)
            border_color = (100, 150, 255)
        else:
            box_color = (100, 0, 0)
            border_color = (255, 100, 100)

        box_rect = pygame.Rect(box_x, box_y, box_width, box_height)
        pygame.draw.rect(self.screen, box_color, box_rect)
        pygame.draw.rect(self.screen, border_color, box_rect, 4)

        # Text
        target_surface = self.font.render(f"{self.reshuffle_target.upper()}", True, (255, 255, 255))
        target_rect = target_surface.get_rect(center=(box_x + box_width // 2, box_y + 35))
        self.screen.blit(target_surface, target_rect)

        shuffle_surface = self.card_font.render("Shuffling discard pile", True, (200, 200, 200))
        shuffle_rect = shuffle_surface.get_rect(center=(box_x + box_width // 2, box_y + 70))
        self.screen.blit(shuffle_surface, shuffle_rect)

        back_surface = self.card_font.render("back into deck...", True, (200, 200, 200))
        back_rect = back_surface.get_rect(center=(box_x + box_width // 2, box_y + 95))
        self.screen.blit(back_surface, back_rect)

    def _render_last_stand_overlay(self) -> None:
        """Render the Last Stand emergency overlay."""
        if not self.last_stand_active:
            return
            
        # Red tint overlay
        overlay = pygame.Surface(self.screen.get_size())
        overlay.set_alpha(50)
        overlay.fill((255, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Warning text
        warning_font = pygame.font.Font(None, 64)
        text_surface = warning_font.render("CRITICAL FAILURE // EMERGENCY SYSTEMS", True, (255, 50, 50))
        text_rect = text_surface.get_rect(center=(self.screen.get_width() // 2, 150))
        # Add a slight pulse or background to make it readable? Simple is fine for now.
        self.screen.blit(text_surface, text_rect)

    def _render_debug_buttons(self, mouse_pos: Tuple[int, int]) -> None:
        """Render debug buttons (Auto-Win, Auto-Lose).

        Args:
            mouse_pos: Current mouse position
        """
        if not self.game_context.debug_mode:
            return

        button_width = 150
        button_height = 60
        button_gap = 20
        debug_x = self.screen.get_width() - button_width - 50
        debug_y_start = 300

        # Reset hover states
        self.debug_win_button_hovered = False
        self.debug_lose_button_hovered = False

        # Auto-win button
        win_rect = pygame.Rect(debug_x, debug_y_start, button_width, button_height)
        win_hovering = win_rect.collidepoint(mouse_pos)
        self.debug_win_button_hovered = win_hovering

        win_color = (0, 200, 0) if win_hovering else (0, 150, 0)
        pygame.draw.rect(self.screen, win_color, win_rect)
        pygame.draw.rect(self.screen, (255, 255, 255), win_rect, 2)

        win_text = self.card_font.render("Auto-Win", True, (255, 255, 255))
        win_text_rect = win_text.get_rect(center=(debug_x + button_width // 2, debug_y_start + button_height // 2))
        self.screen.blit(win_text, win_text_rect)

        # Auto-lose button
        lose_y = debug_y_start + button_height + button_gap
        lose_rect = pygame.Rect(debug_x, lose_y, button_width, button_height)
        lose_hovering = lose_rect.collidepoint(mouse_pos)
        self.debug_lose_button_hovered = lose_hovering

        lose_color = (200, 0, 0) if lose_hovering else (150, 0, 0)
        pygame.draw.rect(self.screen, lose_color, lose_rect)
        pygame.draw.rect(self.screen, (255, 255, 255), lose_rect, 2)

        lose_text = self.card_font.render("Auto-Lose", True, (255, 255, 255))
        lose_text_rect = lose_text.get_rect(center=(debug_x + button_width // 2, lose_y + button_height // 2))
        self.screen.blit(lose_text, lose_text_rect)

    def _render_overlay(self) -> None:
        """Render a semi-transparent dark overlay."""
        overlay = pygame.Surface(self.screen.get_size())
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

    def _render_end_game_modal(self, title: str, title_color: Tuple[int, int, int],
                                bg_color: Tuple[int, int, int],
                                border_color: Tuple[int, int, int]) -> None:
        """Render an end-game modal (victory or defeat).

        Args:
            title: Modal title text
            title_color: Color for the title text
            bg_color: Background color
            border_color: Border color
        """
        self._render_overlay()

        modal_width = 600
        modal_height = 300
        modal_x = (self.screen.get_width() - modal_width) // 2
        modal_y = (self.screen.get_height() - modal_height) // 2

        modal_rect = pygame.Rect(modal_x, modal_y, modal_width, modal_height)
        pygame.draw.rect(self.screen, bg_color, modal_rect)
        pygame.draw.rect(self.screen, border_color, modal_rect, 5)

        # Title
        title_font = pygame.font.Font(None, 72)
        title_surface = title_font.render(title, True, title_color)
        title_rect = title_surface.get_rect(center=(self.screen.get_width() // 2, modal_y + 80))
        self.screen.blit(title_surface, title_rect)

        # Continue instruction
        continue_text = self.card_font.render("Press SPACE or click to continue", True, (200, 200, 200))
        continue_rect = continue_text.get_rect(center=(self.screen.get_width() // 2, modal_y + 200))
        self.screen.blit(continue_text, continue_rect)

    def _render_victory_modal(self) -> None:
        """Render the victory modal."""
        if self.state == CombatState.VICTORY:
            self._render_end_game_modal("VICTORY!", (255, 255, 0), (0, 100, 0), (255, 255, 0))

    def _render_defeat_modal(self) -> None:
        """Render the defeat modal."""
        if self.state == CombatState.DEFEAT:
            self._render_end_game_modal("DEFEAT!", (255, 100, 100), (100, 0, 0), (255, 0, 0))

    def _render_exit_confirmation_modal(self) -> None:
        """Render the exit confirmation modal."""
        if not self.exit_confirmation_modal:
            return

        self._render_overlay()

        modal_width = 600
        modal_height = 250
        modal_x = (self.screen.get_width() - modal_width) // 2
        modal_y = (self.screen.get_height() - modal_height) // 2

        modal_rect = pygame.Rect(modal_x, modal_y, modal_width, modal_height)
        pygame.draw.rect(self.screen, (50, 50, 100), modal_rect)
        pygame.draw.rect(self.screen, (200, 200, 255), modal_rect, 5)

        # Title
        sure_font = pygame.font.Font(None, 56)
        sure_text = sure_font.render("Exit to Menu?", True, (255, 255, 255))
        sure_rect = sure_text.get_rect(center=(self.screen.get_width() // 2, modal_y + 70))
        self.screen.blit(sure_text, sure_rect)

        # Instructions
        enter_text = self.card_font.render("Press ENTER to confirm", True, (150, 255, 150))
        enter_rect = enter_text.get_rect(center=(self.screen.get_width() // 2, modal_y + 140))
        self.screen.blit(enter_text, enter_rect)

        esc_text = self.card_font.render("Press ESC to cancel", True, (255, 150, 150))
        esc_rect = esc_text.get_rect(center=(self.screen.get_width() // 2, modal_y + 180))
        self.screen.blit(esc_text, esc_rect)

    # =========================================================================
    # MAIN RENDER METHOD
    # =========================================================================

    def render(self) -> None:
        """Render the card combat screen."""
        mouse_pos = pygame.mouse.get_pos()
        player_can_act = self._can_player_act()
        layout = self._get_card_layout()

        # Clear screen
        self.screen.fill((0, 0, 64))

        # Render main UI elements
        self._render_hud()
        self._render_hp_displays()
        self._render_decks(layout)
        self._render_player_hand(mouse_pos, player_can_act, layout)
        self._render_action_buttons(mouse_pos, player_can_act, layout)

        # Render cards in motion/staging
        self._render_animating_cards(layout)
        self._render_staged_card(layout)

        # Render overlays and modals
        self._render_discard_modal(mouse_pos)
        self._render_counter_prompt(mouse_pos, layout)
        self._render_enemy_thinking_overlay()
        self._render_reshuffle_overlay()
        self._render_last_stand_overlay()
        self._render_debug_buttons(mouse_pos)

        # Render end-game modals (these include their own overlay)
        self._render_victory_modal()
        self._render_defeat_modal()
        self._render_exit_confirmation_modal()
