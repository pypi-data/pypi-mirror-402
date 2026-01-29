"""
D&D 5e Core - Magic Items System
Implements magic items with combat actions and character enhancements
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Dict, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from ..entities import Character

from .equipment import Equipment, Cost, EquipmentCategory


class MagicItemRarity(Enum):
    """Rarity levels for magic items"""
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    VERY_RARE = "very rare"
    LEGENDARY = "legendary"
    ARTIFACT = "artifact"


class MagicItemType(Enum):
    """Types of magic items"""
    WEAPON = "weapon"
    ARMOR = "armor"
    POTION = "potion"
    RING = "ring"
    WAND = "wand"
    STAFF = "staff"
    ROD = "rod"
    WONDROUS = "wondrous"
    SCROLL = "scroll"


@dataclass
class MagicItemEffect:
    """Effect applied by a magic item"""
    name: str
    description: str
    effect_type: str  # "ac_bonus", "saving_throw_bonus", "ability_bonus", "damage", "healing", "condition"
    value: int = 0
    duration: Optional[int] = None  # Duration in rounds, None = permanent
    conditions: List[str] = field(default_factory=list)  # Conditions applied


@dataclass
class MagicItemAction:
    """
    Action that can be performed with a magic item in combat
    Similar to weapon attacks or spell casting
    """
    name: str
    description: str
    action_type: str  # "attack", "healing", "defense", "utility"
    damage_dice: Optional[str] = None  # e.g., "3d6"
    damage_type: Optional[str] = None  # fire, cold, etc.
    healing_dice: Optional[str] = None  # e.g., "2d4+2"
    range: int = 5  # Range in feet
    area_of_effect: Optional[str] = None  # "cone", "sphere", etc.
    save_dc: Optional[int] = None  # Saving throw DC
    save_ability: Optional[str] = None  # "dex", "con", etc.
    uses_per_day: Optional[int] = None  # Limited uses, None = unlimited
    recharge: Optional[str] = None  # "dawn", "short rest", "long rest"

    def __post_init__(self):
        """Initialize tracking for limited uses"""
        self.remaining_uses = self.uses_per_day if self.uses_per_day else None


@dataclass
class MagicItem(Equipment):
    """
    Magic Item with special properties and combat actions

    Magic items can:
    - Provide stat bonuses (AC, saving throws, abilities)
    - Be used for combat actions (attacks, healing, defense)
    - Grant special abilities or conditions
    - Require attunement
    """
    rarity: MagicItemRarity
    item_type: MagicItemType
    requires_attunement: bool = False
    attuned: bool = False

    # Passive bonuses (always active when equipped/attuned)
    ac_bonus: int = 0
    saving_throw_bonus: int = 0
    ability_bonuses: Dict[str, int] = field(default_factory=dict)  # {"str": 2, "dex": 1}

    # Active abilities (can be used in combat)
    actions: List[MagicItemAction] = field(default_factory=list)

    # Passive effects
    effects: List[MagicItemEffect] = field(default_factory=list)

    def can_use(self) -> bool:
        """Check if item can be used (attuned if required, equipped)"""
        if self.requires_attunement and not self.attuned:
            return False
        return self.equipped

    def can_perform_action(self, action: MagicItemAction) -> bool:
        """Check if a specific action can be performed"""
        if not self.can_use():
            return False

        if action.remaining_uses is not None and action.remaining_uses <= 0:
            return False

        return True

    def use_action(self, action: MagicItemAction) -> bool:
        """Use an action, consuming charges if limited"""
        if not self.can_perform_action(action):
            return False

        if action.remaining_uses is not None:
            action.remaining_uses -= 1

        return True

    def recharge_actions(self, recharge_type: str = "long rest"):
        """
        Recharge limited use actions

        Args:
            recharge_type: "dawn", "short rest", "long rest"
        """
        for action in self.actions:
            if action.recharge == recharge_type or (action.recharge == "dawn" and recharge_type == "long rest"):
                action.remaining_uses = action.uses_per_day

    def attune(self, character: 'Character') -> bool:
        """
        Attune this item to a character

        Args:
            character: Character to attune to

        Returns:
            True if successfully attuned
        """
        if not self.requires_attunement:
            return True

        # Check attunement limit (typically 3 items)
        if hasattr(character, 'attuned_items'):
            if len([i for i in character.attuned_items if i.attuned]) >= 3:
                return False

        self.attuned = True
        return True

    def unattune(self):
        """Remove attunement"""
        self.attuned = False

    def apply_to_character(self, character: 'Character'):
        """
        Apply passive bonuses to character

        This modifies the character's stats while the item is equipped
        """
        if not self.can_use():
            return

        # Apply AC bonus (Character already has ac_bonus attribute)
        if self.ac_bonus > 0:
            if not hasattr(character, 'ac_bonus'):
                character.ac_bonus = 0
            character.ac_bonus += self.ac_bonus

        # Apply ability bonuses
        for ability, bonus in self.ability_bonuses.items():
            if hasattr(character.abilities, ability):
                current = getattr(character.abilities, ability)
                setattr(character.abilities, ability, current + bonus)

                # Update modifiers too
                if hasattr(character, 'ability_modifiers'):
                    mod = (current + bonus - 10) // 2
                    setattr(character.ability_modifiers, ability, mod)

    def remove_from_character(self, character: 'Character'):
        """
        Remove passive bonuses from character

        This is called when unequipping the item
        """
        if not self.equipped:
            return

        # Remove AC bonus
        if self.ac_bonus > 0:
            if hasattr(character, 'ac_bonus'):
                character.ac_bonus -= self.ac_bonus

        # Remove ability bonuses
        for ability, bonus in self.ability_bonuses.items():
            if hasattr(character.abilities, ability):
                current = getattr(character.abilities, ability)
                setattr(character.abilities, ability, current - bonus)

                # Update modifiers too
                if hasattr(character, 'ability_modifiers'):
                    mod = (current - bonus - 10) // 2
                    setattr(character.ability_modifiers, ability, mod)

    def __repr__(self):
        attune_str = " (attuned)" if self.attuned else " (requires attunement)" if self.requires_attunement else ""
        return f"{self.name} ({self.rarity.value}){attune_str}"


def create_magic_item_from_data(data: dict) -> Optional[MagicItem]:
    """
    Create a MagicItem from API/JSON data

    Args:
        data: Dictionary with magic item data

    Returns:
        MagicItem instance or None
    """
    try:
        # Extract basic info
        index = data.get('index', '')
        name = data.get('name', '')
        desc = data.get('desc', [])

        # Parse description to extract rarity and attunement
        desc_text = ' '.join(desc) if isinstance(desc, list) else desc
        desc_lower = desc_text.lower()

        # Determine rarity
        rarity = MagicItemRarity.COMMON
        for r in MagicItemRarity:
            if r.value in desc_lower:
                rarity = r
                break

        # Check attunement
        requires_attunement = 'attunement' in desc_lower

        # Determine type from category
        category_data = data.get('equipment_category', {})
        category_index = category_data.get('index', 'wondrous-items')

        item_type = MagicItemType.WONDROUS
        if 'weapon' in category_index:
            item_type = MagicItemType.WEAPON
        elif 'armor' in category_index:
            item_type = MagicItemType.ARMOR
        elif 'potion' in category_index:
            item_type = MagicItemType.POTION
        elif 'ring' in category_index:
            item_type = MagicItemType.RING
        elif 'wand' in category_index:
            item_type = MagicItemType.WAND
        elif 'staff' in category_index:
            item_type = MagicItemType.STAFF
        elif 'rod' in category_index:
            item_type = MagicItemType.ROD

        # Create category
        category = EquipmentCategory(
            index=category_index,
            name=category_data.get('name', 'Magic Item'),
            url=category_data.get('url', '')
        )

        # Default cost (magic items are expensive!)
        cost = Cost(quantity=100, unit='gp')

        # Parse for bonuses (basic parsing)
        ac_bonus = 0
        saving_throw_bonus = 0
        ability_bonuses = {}

        if '+1 bonus to ac' in desc_lower or '+1 to ac' in desc_lower:
            ac_bonus = 1
        elif '+2 bonus to ac' in desc_lower or '+2 to ac' in desc_lower:
            ac_bonus = 2
        elif '+3 bonus to ac' in desc_lower or '+3 to ac' in desc_lower:
            ac_bonus = 3

        if '+1 bonus to' in desc_lower and 'saving throw' in desc_lower:
            saving_throw_bonus = 1
        elif '+2 bonus to' in desc_lower and 'saving throw' in desc_lower:
            saving_throw_bonus = 2

        return MagicItem(
            index=index,
            name=name,
            cost=cost,
            weight=data.get('weight', 1),
            desc=desc,
            category=category,
            equipped=False,
            rarity=rarity,
            item_type=item_type,
            requires_attunement=requires_attunement,
            attuned=False,
            ac_bonus=ac_bonus,
            saving_throw_bonus=saving_throw_bonus,
            ability_bonuses=ability_bonuses,
            actions=[],
            effects=[]
        )

    except Exception as e:
        print(f"Error creating magic item from data: {e}")
        return None


__all__ = [
    'MagicItem',
    'MagicItemRarity',
    'MagicItemType',
    'MagicItemEffect',
    'MagicItemAction',
    'create_magic_item_from_data',
]

