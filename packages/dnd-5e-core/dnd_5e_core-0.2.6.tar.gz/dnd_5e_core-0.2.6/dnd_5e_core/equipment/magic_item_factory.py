"""
D&D 5e Core - Magic Item Creation Helpers
Helper functions to create magic items with conditions and effects
"""
from typing import List, Optional

from .magic_item import MagicItem, MagicItemAction, MagicItemRarity, MagicItemType, MagicItemEffect
from ..combat.condition import Condition
from ..combat.condition_parser import ConditionParser
from .equipment import Cost, EquipmentCategory


def create_magic_item_with_conditions(
    name: str,
    description: str,
    rarity: MagicItemRarity,
    item_type: MagicItemType,
    action_name: str = None,
    action_description: str = "",
    damage_dice: str = None,
    damage_type: str = None,
    save_dc: int = None,
    save_ability: str = None,
    uses_per_day: int = None,
    recharge: str = None,
    requires_attunement: bool = False,
    ac_bonus: int = 0,
    weight: float = 0.0,
    cost: int = 0
) -> MagicItem:
    """
    Create a magic item with automatic condition parsing.

    Args:
        name: Item name
        description: Item description
        rarity: Item rarity
        item_type: Type of magic item
        action_name: Name of the action (if item has active ability)
        action_description: Description of the action (parsed for conditions)
        damage_dice: Damage dice (e.g., "3d6")
        damage_type: Type of damage
        save_dc: Saving throw DC
        save_ability: Ability for saving throw
        uses_per_day: Limited uses per day
        recharge: When item recharges ("dawn", "short rest", "long rest")
        requires_attunement: Whether item requires attunement
        ac_bonus: AC bonus provided
        weight: Item weight
        cost: Item cost in gp

    Returns:
        MagicItem with parsed conditions
    """
    # Parse conditions from description
    conditions = ConditionParser.parse_condition_from_description(
        action_description if action_description else description
    )

    # Create action if applicable
    actions = []
    if action_name:
        action_type = "attack" if damage_dice else "utility"

        action = MagicItemAction(
            name=action_name,
            description=action_description,
            action_type=action_type,
            damage_dice=damage_dice,
            damage_type=damage_type,
            save_dc=save_dc,
            save_ability=save_ability,
            uses_per_day=uses_per_day,
            recharge=recharge,
            conditions=conditions
        )
        actions.append(action)

    # Create the magic item
    return MagicItem(
        index=name.lower().replace(" ", "-"),
        name=name,
        desc=[description] if isinstance(description, str) else description,
        weight=weight,
        cost=Cost(quantity=cost, unit='gp'),
        category=EquipmentCategory(
            index=item_type.value,
            name=item_type.value.title(),
            url=f"/api/equipment-categories/{item_type.value}"
        ),
        rarity=rarity,
        item_type=item_type,
        requires_attunement=requires_attunement,
        ac_bonus=ac_bonus,
        actions=actions,
        equipped=False
    )


# Pre-built magic items with conditions

def create_wand_of_paralysis() -> MagicItem:
    """Create a Wand of Paralysis that can paralyze targets"""
    return create_magic_item_with_conditions(
        name="Wand of Paralysis",
        description="This wand can paralyze a creature for 1 minute.",
        rarity=MagicItemRarity.RARE,
        item_type=MagicItemType.WAND,
        action_name="Paralyze",
        action_description="Target must make a DC 15 Constitution saving throw or be paralyzed for 1 minute. "
                          "The target can repeat the saving throw at the end of each of its turns.",
        save_dc=15,
        save_ability="con",
        uses_per_day=3,
        recharge="dawn",
        requires_attunement=True,
        weight=1.0,
        cost=5000
    )


def create_staff_of_entanglement() -> MagicItem:
    """Create a Staff that restrains creatures"""
    return create_magic_item_with_conditions(
        name="Staff of Entanglement",
        description="This staff can entangle and restrain foes.",
        rarity=MagicItemRarity.UNCOMMON,
        item_type=MagicItemType.STAFF,
        action_name="Entangle",
        action_description="Target must make a DC 13 Strength saving throw or be restrained by magical vines. "
                          "The target can use its action to make a DC 13 Strength check to break free.",
        save_dc=13,
        save_ability="str",
        uses_per_day=5,
        recharge="dawn",
        requires_attunement=False,
        weight=4.0,
        cost=500
    )


def create_ring_of_blinding() -> MagicItem:
    """Create a Ring that can blind targets"""
    return create_magic_item_with_conditions(
        name="Ring of Blinding",
        description="This ring can emit a flash of light to blind enemies.",
        rarity=MagicItemRarity.UNCOMMON,
        item_type=MagicItemType.RING,
        action_name="Blinding Flash",
        action_description="Target must make a DC 14 Constitution saving throw or be blinded for 1 minute.",
        save_dc=14,
        save_ability="con",
        uses_per_day=2,
        recharge="long rest",
        requires_attunement=True,
        weight=0.1,
        cost=800
    )


def create_cloak_of_fear() -> MagicItem:
    """Create a Cloak that frightens enemies"""
    return create_magic_item_with_conditions(
        name="Cloak of Fear",
        description="This cloak can instill fear in nearby creatures.",
        rarity=MagicItemRarity.RARE,
        item_type=MagicItemType.WONDROUS,
        action_name="Aura of Terror",
        action_description="Creatures within 30 feet must make a DC 15 Wisdom saving throw or be frightened "
                          "for 1 minute. A frightened creature can repeat the saving throw at the end of each turn.",
        save_dc=15,
        save_ability="wis",
        uses_per_day=1,
        recharge="long rest",
        requires_attunement=True,
        weight=1.0,
        cost=3000
    )


def create_poisoned_dagger() -> MagicItem:
    """Create a magical dagger that poisons on hit"""
    return create_magic_item_with_conditions(
        name="Poisoned Dagger +1",
        description="This magical dagger is coated with a potent poison.",
        rarity=MagicItemRarity.UNCOMMON,
        item_type=MagicItemType.WEAPON,
        action_name="Poison Strike",
        action_description="On hit, target takes 2d8 poison damage and must make a DC 13 Constitution saving throw "
                          "or be poisoned for 1 hour.",
        damage_dice="2d8",
        damage_type="poison",
        save_dc=13,
        save_ability="con",
        uses_per_day=3,
        recharge="dawn",
        requires_attunement=False,
        weight=1.0,
        cost=1000
    )
