"""
D&D 5e Core - Equipment Module
Contains all equipment classes (weapons, armor, potions, magic items, etc.)
"""

from .equipment import Cost, EquipmentCategory, Equipment, Inventory
from .potion import PotionRarity, Potion, HealingPotion, SpeedPotion, StrengthPotion
from .weapon import (
    CategoryType, RangeType, DamageType,
    WeaponProperty, WeaponRange, WeaponThrowRange, Weapon
)
from .armor import Armor
from .magic_item import (
    MagicItem, MagicItemRarity, MagicItemType,
    MagicItemEffect, MagicItemAction, create_magic_item_from_data
)
from .predefined_magic_items import (
    create_ring_of_protection, create_cloak_of_protection,
    create_wand_of_magic_missiles, create_staff_of_healing,
    create_belt_of_giant_strength, create_amulet_of_health,
    create_bracers_of_defense, create_necklace_of_fireballs,
    get_magic_item, PREDEFINED_MAGIC_ITEMS
)
from .magic_item_factory import (
    create_magic_item_with_conditions,
    create_wand_of_paralysis, create_staff_of_entanglement,
    create_ring_of_blinding, create_cloak_of_fear,
    create_poisoned_dagger
)

__all__ = [
    # Base equipment
    'Cost', 'EquipmentCategory', 'Equipment', 'Inventory',
    # Potions
    'PotionRarity', 'Potion', 'HealingPotion', 'SpeedPotion', 'StrengthPotion',
    # Weapon types
    'CategoryType', 'RangeType', 'DamageType',
    'WeaponProperty', 'WeaponRange', 'WeaponThrowRange', 'Weapon',
    # Armor
    'Armor',
    # Magic Items
    'MagicItem', 'MagicItemRarity', 'MagicItemType',
    'MagicItemEffect', 'MagicItemAction', 'create_magic_item_from_data',
    # Predefined Magic Items
    'create_ring_of_protection', 'create_cloak_of_protection',
    'create_wand_of_magic_missiles', 'create_staff_of_healing',
    'create_belt_of_giant_strength', 'create_amulet_of_health',
    'create_bracers_of_defense', 'create_necklace_of_fireballs',
    'get_magic_item', 'PREDEFINED_MAGIC_ITEMS',
    # Magic Items with Conditions
    'create_magic_item_with_conditions',
    'create_wand_of_paralysis', 'create_staff_of_entanglement',
    'create_ring_of_blinding', 'create_cloak_of_fear',
    'create_poisoned_dagger',
]

