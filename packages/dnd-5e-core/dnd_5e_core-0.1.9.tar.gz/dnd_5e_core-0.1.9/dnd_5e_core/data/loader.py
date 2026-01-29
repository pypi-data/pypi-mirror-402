"""
D&D 5e Core - Data Loader
Functions to load D&D 5e data from local JSON files and return entity objects

This module provides functions to load game data (monsters, spells, weapons, armor)
from local JSON files and convert them into proper entity objects (Monster, Spell, etc.)
instead of raw dictionaries.

Example:
    >>> from dnd_5e_core.data import load_monster, load_spell
    >>>
    >>> # Load a monster object
    >>> goblin = load_monster("goblin")
    >>> print(f"{goblin.name} - CR {goblin.challenge_rating}")
    >>>
    >>> # Load a spell object
    >>> fireball = load_spell("fireball")
    >>> print(f"{fireball.name} - Level {fireball.level}")
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Optional, List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..entities.monster import Monster
    from ..spells.spell import Spell
    from ..equipment.weapon import Weapon
    from ..equipment.armor import Armor


# Default data directory (can be overridden)
_DATA_DIR = None


def set_data_directory(path: str):
    """
    Set the data directory path.

    Args:
        path: Path to the data directory containing JSON files
    """
    global _DATA_DIR
    _DATA_DIR = Path(path)


def get_data_directory() -> Path:
    """
    Get the data directory path.

    Returns:
        Path to data directory
    """
    global _DATA_DIR

    if _DATA_DIR is None:
        # Try to find data directory automatically
        current_file = Path(__file__)

        # Try common locations
        possible_paths = [
            # If data is in the dnd-5e-core package itself (preferred)
            current_file.parent.parent.parent / "data",
            # If used from DnD-5th-Edition-API project (fallback)
            current_file.parent.parent.parent.parent.parent / "DnD-5th-Edition-API" / "data",
            # If data is in current working directory
            Path.cwd() / "data",
        ]

        for path in possible_paths:
            if path.exists() and path.is_dir():
                _DATA_DIR = path
                break

        if _DATA_DIR is None:
            raise FileNotFoundError(
                "Data directory not found. Please use set_data_directory() to specify the path."
            )

    return _DATA_DIR


def load_json_file(category: str, index: str) -> Optional[Dict[str, Any]]:
    """
    Load a JSON file from the data directory.

    Args:
        category: Category (e.g., "monsters", "spells", "weapons")
        index: Item index/name (e.g., "goblin", "fireball")

    Returns:
        Dict with data or None on error
    """
    try:
        data_dir = get_data_directory()
        file_path = data_dir / category / f"{index}.json"

        if not file_path.exists():
            # Silently return None for files not found (e.g., magic items in equipment collection)
            return None

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return data
    except Exception as e:
        # Only print error if DEBUG mode is enabled
        if os.getenv('DEBUG'):
            print(f"Error loading {category}/{index}: {e}")
        return None


def list_json_files(category: str) -> List[str]:
    """
    List all JSON files in a category.

    Args:
        category: Category (e.g., "monsters", "spells")

    Returns:
        List of indices (without .json extension)
    """
    try:
        data_dir = get_data_directory()
        category_dir = data_dir / category

        if not category_dir.exists():
            return []

        return [
            f.stem for f in category_dir.glob("*.json")
            if f.is_file()
        ]
    except Exception as e:
        print(f"Error listing {category}: {e}")
        return []


# ===== Helper Functions to Create Objects from JSON Data =====

def _create_monster_from_data(index: str, data: Dict[str, Any]) -> Optional['Monster']:
    """
    Create a Monster object from JSON data.

    Args:
        index: Monster index
        data: Monster JSON data

    Returns:
        Monster object
    """
    from ..entities.monster import Monster
    from ..abilities.abilities import Abilities
    from ..classes.proficiency import Proficiency, ProfType
    from ..combat.action import Action, ActionType
    from ..combat.damage import Damage
    from ..equipment.weapon import DamageType
    from ..mechanics.dice import DamageDice
    from ..spells.spell import Spell
    from ..spells.spellcaster import SpellCaster
    from ..combat.special_ability import SpecialAbility, AreaOfEffect

    # Abilities
    abilities = Abilities(
        str=data.get('strength', 10),
        dex=data.get('dexterity', 10),
        con=data.get('constitution', 10),
        int=data.get('intelligence', 10),
        wis=data.get('wisdom', 10),
        cha=data.get('charisma', 10)
    )

    # Proficiencies
    proficiencies: List[Proficiency] = []
    if 'proficiencies' in data:
        for prof_data in data['proficiencies']:
            prof_index = prof_data['proficiency']['index']
            prof_name = prof_data['proficiency'].get('name', prof_index)

            # Déterminer le type de proficiency
            prof_type = None
            if 'skill' in prof_index:
                prof_type = ProfType.SKILL
            elif 'saving-throw' in prof_index:
                prof_type = ProfType.ST
            elif 'weapon' in prof_index or prof_index in ['simple-weapons', 'martial-weapons']:
                prof_type = ProfType.WEAPON
            elif 'armor' in prof_index or prof_index in ['light-armor', 'medium-armor', 'heavy-armor', 'shields']:
                prof_type = ProfType.ARMOR
            else:
                prof_type = ProfType.OTHER

            prof = Proficiency(
                index=prof_index,
                name=prof_name,
                type=prof_type,
                ref=None,  # Pas de référence spécifique pour les monstres
                value=prof_data.get('value', 0)
            )
            proficiencies.append(prof)

    # Special abilities & Spellcasting
    special_abilities: List[SpecialAbility] = []
    spell_caster: Optional[SpellCaster] = None

    if "special_abilities" in data:
        for special_ability in data['special_abilities']:
            action_name: str = special_ability['name']

            # Spellcasting
            if special_ability['name'] == 'Spellcasting':
                ability: dict = special_ability['spellcasting']
                caster_level = ability['level']
                dc_type = ability['ability']['index']
                dc_value = ability['dc']
                ability_modifier = ability['modifier']
                slots = [s for s in ability['slots'].values()]
                spells: List[Spell] = []

                for spell_dict in ability['spells']:
                    spell_index_name: str = spell_dict['url'].split('/')[3]
                    spell = load_spell(spell_index_name)
                    if spell is not None:
                        spells.append(spell)

                if spells:
                    spell_caster = SpellCaster(
                        level=caster_level,
                        spell_slots=slots,
                        learned_spells=spells,
                        dc_type=dc_type,
                        dc_value=dc_value + ability_modifier,
                        ability_modifier=ability_modifier
                    )

            # Special abilities with damage
            elif 'damage' in special_ability:
                damages: List[Damage] = []
                for damage in special_ability['damage']:
                    if "damage_type" in damage:
                        damage_type = DamageType(
                            index=damage['damage_type']['index'],
                            name=damage['damage_type'].get('name', damage['damage_type']['index']),
                            desc=f"{damage['damage_type']['index']} damage"
                        )

                        damage_dice_str = damage['damage_dice']
                        if '+' in damage_dice_str:
                            dice_part, bonus = damage_dice_str.split('+')
                            dd = DamageDice(dice_part.strip(), int(bonus))
                        elif '-' in damage_dice_str:
                            dice_part, bonus = damage_dice_str.split('-')
                            dd = DamageDice(dice_part.strip(), -int(bonus))
                        else:
                            dd = DamageDice(damage_dice_str)

                        damages.append(Damage(type=damage_type, dd=dd))

                # Extract DC info
                dc_type = None
                dc_value = None
                dc_success = None
                if 'dc' in special_ability:
                    dc_type = special_ability['dc']['dc_type']['index']
                    dc_value = special_ability['dc']['dc_value']
                    dc_success = special_ability['dc'].get('success_type')

                # Area of effect
                area_of_effect: Optional[AreaOfEffect] = None
                if 'area_of_effect' in special_ability:
                    aoe_data = special_ability['area_of_effect']
                    area_of_effect = AreaOfEffect(
                        type=aoe_data.get('type', 'sphere'),
                        size=aoe_data.get('size', 15)
                    )

                if damages:
                    special_abilities.append(SpecialAbility(
                        name=action_name,
                        desc=special_ability.get('desc', ''),
                        damages=damages,
                        dc_type=dc_type,
                        dc_value=dc_value,
                        dc_success=dc_success,
                        recharge_on_roll=None,
                        area_of_effect=area_of_effect
                    ))

    # Actions
    actions: List[Action] = []

    if "actions" in data:
        for action in data['actions']:
            # Skip Multiattack for now (will handle separately)
            if action['name'] != 'Multiattack':
                if "damage" in action:
                    normal_range = long_range = 5
                    is_melee_attack = re.search("Melee.*Attack", action.get('desc', ''))
                    is_ranged_attack = re.search("Ranged.*Attack", action.get('desc', ''))

                    # Extract range for ranged attacks
                    if is_ranged_attack:
                        range_pattern = r"range\s+(\d+)/(\d+)\s*ft\."
                        match = re.search(range_pattern, action.get('desc', ''))
                        if match:
                            normal_range = int(match.group(1))
                            long_range = int(match.group(2))
                        else:
                            normal_range = 5
                            long_range = None

                    damages: List[Damage] = []
                    for damage in action['damage']:
                        if "damage_type" in damage:
                            damage_type = DamageType(
                                index=damage['damage_type']['index'],
                                name=damage['damage_type'].get('name', damage['damage_type']['index']),
                                desc=f"{damage['damage_type']['index']} damage"
                            )
                            dd = DamageDice(damage['damage_dice'])
                            damages.append(Damage(type=damage_type, dd=dd))

                    if damages:
                        action_type = ActionType.MIXED if is_melee_attack and is_ranged_attack else ActionType.MELEE if is_melee_attack else ActionType.RANGED
                        actions.append(Action(
                            name=action['name'],
                            desc=action.get('desc', ''),
                            type=action_type,
                            normal_range=normal_range,
                            long_range=long_range,
                            attack_bonus=action.get('attack_bonus'),
                            multi_attack=None,
                            damages=damages
                        ))

            # Handle special abilities with DC
            elif 'dc' in action:
                if 'damage' in action:
                    damages: List[Damage] = []
                    for damage in action['damage']:
                        if "damage_type" in damage:
                            damage_type = DamageType(
                                index=damage['damage_type']['index'],
                                name=damage['damage_type'].get('name', damage['damage_type']['index']),
                                desc=f"{damage['damage_type']['index']} damage"
                            )
                            dd = DamageDice(damage['damage_dice'])
                            damages.append(Damage(type=damage_type, dd=dd))

                    dc_type = action['dc']['dc_type']['index']
                    dc_value = action['dc']['dc_value']
                    dc_success = action['dc'].get('success_type')

                    # Extract recharge info
                    recharge_on_roll = None
                    if 'usage' in action and 'dice' in action['usage']:
                        recharge_on_roll = action['usage']['min_value']

                    if damages:
                        special_abilities.append(SpecialAbility(
                            name=action['name'],
                            desc=action.get('desc', ''),
                            damages=damages,
                            dc_type=dc_type,
                            dc_value=dc_value,
                            dc_success=dc_success,
                            recharge_on_roll=recharge_on_roll,
                            area_of_effect=None
                        ))

        # Handle Multiattack
        for action in data['actions']:
            if action['name'] == 'Multiattack' and 'options' in action:
                multi_attack: List[Action] = []
                choose_count = action['options']['choose']

                for action_dict in action['options']['from'][0]:
                    try:
                        count = int(action_dict['count'])
                        action_match = next((a for a in actions if a.name == action_dict['name']), None)
                        if action_match and action_match.type in {ActionType.MELEE, ActionType.RANGED}:
                            multi_attack.extend([action_match] * count)
                    except (ValueError, KeyError):
                        if os.getenv('DEBUG'):
                            print(f"Invalid count option for {index}: {action_dict.get('name')}")

                if multi_attack:
                    actions.append(Action(
                        name=action['name'],
                        desc=action.get('desc', ''),
                        type=ActionType.MELEE,
                        attack_bonus=0,  # Multiattack uses the sub-actions' bonuses
                        multi_attack=multi_attack,
                        damages=None
                    ))

    # Speed
    speed_data = data.get('speed', {})
    speed_str = speed_data.get('fly') or speed_data.get('walk') or '30 ft.'
    speed = int(speed_str.split()[0])

    # Create Monster
    return Monster(
        index=index,
        name=data['name'],
        abilities=abilities,
        proficiencies=proficiencies,
        armor_class=data.get('armor_class', 10),
        hit_points=data.get('hit_points', 1),
        hit_dice=data.get('hit_dice', '1d8'),
        xp=data.get('xp', 0),
        speed=speed,
        challenge_rating=parse_challenge_rating(data.get('challenge_rating', 0)),
        actions=actions,
        sc=spell_caster,
        sa=special_abilities if special_abilities else None
    )


def _create_spell_from_data(index: str, data: Dict[str, Any]) -> Optional['Spell']:
    """
    Create a Spell object from JSON data.

    Args:
        index: Spell index
        data: Spell JSON data

    Returns:
        Spell object
    """
    from ..spells.spell import Spell
    from ..equipment.weapon import DamageType
    from ..combat.special_ability import AreaOfEffect

    # Damage (if applicable)
    damage_type = None
    damage_at_slot_level = None
    damage_at_character_level = None

    if 'damage' in data:
        if 'damage_type' in data['damage']:
            damage_type = DamageType(
                index=data['damage']['damage_type']['index'],
                name=data['damage']['damage_type'].get('name', data['damage']['damage_type']['index']),
                desc=f"{data['damage']['damage_type']['index']} damage"
            )

        if 'damage_at_slot_level' in data['damage']:
            damage_at_slot_level = data['damage']['damage_at_slot_level']

        if 'damage_at_character_level' in data['damage']:
            damage_at_character_level = data['damage']['damage_at_character_level']

    # Healing
    heal_at_slot_level = None
    if 'heal_at_slot_level' in data:
        heal_at_slot_level = data['heal_at_slot_level']

    # DC info
    dc_type = None
    dc_success = None
    if 'dc' in data:
        dc_type = data['dc']['dc_type']['index']
        dc_success = data['dc'].get('dc_success')

    # Area of effect
    area_of_effect = None
    if 'area_of_effect' in data:
        aoe_data = data['area_of_effect']
        area_of_effect = AreaOfEffect(
            type=aoe_data.get('type', 'sphere'),
            size=aoe_data.get('size', 15)
        )

    # Range
    range_value = data.get('range', 'Self')
    if isinstance(range_value, str):
        # Extract number from strings like "120 feet" or "Self"
        import re
        match = re.search(r'(\d+)', range_value)
        range_ft = int(match.group(1)) if match else 0
    else:
        range_ft = int(range_value)

    return Spell(
        index=index,
        name=data['name'],
        desc='\n'.join(data.get('desc', [])),
        level=data.get('level', 0),
        allowed_classes=[c['index'] for c in data.get('classes', [])],
        heal_at_slot_level=heal_at_slot_level,
        damage_type=damage_type,
        damage_at_slot_level=damage_at_slot_level,
        damage_at_character_level=damage_at_character_level,
        dc_type=dc_type,
        dc_success=dc_success,
        range=range_ft,
        area_of_effect=area_of_effect,
        school=data.get('school', {}).get('index', 'evocation')
    )


# ===== Loader Functions =====

def load_monster(index: str) -> Optional['Monster']:
    """
    Load monster data from local JSON file and return a Monster object.

    Args:
        index: Monster index (e.g., "goblin", "ancient-red-dragon")

    Returns:
        Monster object or None
    """
    data = load_json_file("monsters", index)
    if data is None:
        return None

    return _create_monster_from_data(index, data)


def load_spell(index: str) -> Optional['Spell']:
    """
    Load spell data from local JSON file and return a Spell object.

    Args:
        index: Spell index (e.g., "fireball", "magic-missile")

    Returns:
        Spell object or None
    """
    data = load_json_file("spells", index)
    if data is None:
        return None

    return _create_spell_from_data(index, data)


def load_weapon(index: str) -> Optional['Weapon']:
    """
    Load weapon data from local JSON file and return a Weapon object.

    Args:
        index: Weapon index (e.g., "longsword", "dagger")

    Returns:
        Weapon object or None
    """
    data = load_json_file("equipment", index)
    if data is None or data.get('equipment_category', {}).get('index') != 'weapon':
        # Try weapons collection
        data = load_json_file("weapons", index)
        if data is None:
            return None

    from ..equipment.weapon import Weapon, DamageType, WeaponProperty, WeaponRange, RangeType, CategoryType
    from ..equipment.equipment import Cost, EquipmentCategory
    from ..mechanics.dice import DamageDice

    # Damage type
    damage_type = DamageType(
        index='slashing',
        name='Slashing',
        desc='slashing damage'
    )
    if 'damage' in data and 'damage_type' in data['damage']:
        damage_type = DamageType(
            index=data['damage']['damage_type']['index'],
            name=data['damage']['damage_type'].get('name', data['damage']['damage_type']['index']),
            desc=f"{data['damage']['damage_type']['index']} damage"
        )

    # Range
    weapon_range = None
    if 'range' in data:
        normal_range = data['range'].get('normal', 5)
        long_range = data['range'].get('long')
        weapon_range = WeaponRange(normal=normal_range, long=long_range)

    # Properties
    properties = []
    for prop_data in data.get('properties', []):
        prop = WeaponProperty(
            index=prop_data.get('index', ''),
            name=prop_data.get('name', prop_data.get('index', '')),
            desc=prop_data.get('desc', '')
        )
        properties.append(prop)

    # Range type and category type
    weapon_range_str = data.get('weapon_range', 'Melee')
    range_type = RangeType.RANGED if weapon_range_str == 'Ranged' else RangeType.MELEE

    weapon_category_str = data.get('weapon_category', 'Simple')
    category_type = CategoryType.MARTIAL if weapon_category_str == 'Martial' else CategoryType.SIMPLE

    # Damage dice
    damage_dice = DamageDice(data.get('damage', {}).get('damage_dice', '1d4'))

    # Two-handed damage (if versatile)
    damage_dice_two_handed = None
    if '2h_damage' in data:
        damage_dice_two_handed = DamageDice(data['2h_damage'].get('damage_dice', '1d4'))

    return Weapon(
        index=index,
        name=data['name'],
        desc=data.get('desc') if isinstance(data.get('desc'), list) else None,
        category=EquipmentCategory(
            index=data.get('equipment_category', {}).get('index', 'weapon'),
            name=data.get('equipment_category', {}).get('name', 'Weapon'),
            url=data.get('equipment_category', {}).get('url', '/api/equipment-categories/weapon')
        ),
        cost=Cost(
            quantity=data.get('cost', {}).get('quantity', 0),
            unit=data.get('cost', {}).get('unit', 'gp')
        ),
        weight=data.get('weight', 0),
        equipped=False,
        properties=properties,
        damage_type=damage_type,
        range_type=range_type,
        category_type=category_type,
        damage_dice=damage_dice,
        damage_dice_two_handed=damage_dice_two_handed,
        weapon_range=weapon_range
    )


def load_armor(index: str) -> Optional['Armor']:
    """
    Load armor data from local JSON file and return an Armor object.

    Args:
        index: Armor index (e.g., "plate-armor", "chain-mail")

    Returns:
        Armor object or None
    """
    data = load_json_file("equipment", index)
    if data is None or data.get('equipment_category', {}).get('index') != 'armor':
        # Try armors collection
        data = load_json_file("armors", index)
        if data is None:
            return None

    from ..equipment.armor import Armor
    from ..equipment.equipment import Cost, EquipmentCategory

    # AC info
    armor_class = data.get('armor_class', {'base': 10})

    # Strength requirement
    str_minimum = data.get('str_minimum', 0)

    # Stealth disadvantage
    stealth_disadvantage = data.get('stealth_disadvantage', False)

    return Armor(
        index=index,
        name=data['name'],
        desc=data.get('desc') if isinstance(data.get('desc'), list) else None,
        category=EquipmentCategory(
            index=data.get('equipment_category', {}).get('index', 'armor'),
            name=data.get('equipment_category', {}).get('name', 'Armor'),
            url=data.get('equipment_category', {}).get('url', '/api/equipment-categories/armor')
        ),
        cost=Cost(
            quantity=data.get('cost', {}).get('quantity', 0),
            unit=data.get('cost', {}).get('unit', 'gp')
        ),
        weight=data.get('weight', 0),
        equipped=False,
        armor_class=armor_class,
        str_minimum=str_minimum,
        stealth_disadvantage=stealth_disadvantage
    )


def load_race(index: str) -> Optional[Dict[str, Any]]:
    """
    Load race data from local JSON file.

    Args:
        index: Race index (e.g., "elf", "dwarf", "human")

    Returns:
        Dict with race data or None
    """
    return load_json_file("races", index)


def load_class(index: str) -> Optional[Dict[str, Any]]:
    """
    Load class data from local JSON file.

    Args:
        index: Class index (e.g., "fighter", "wizard", "rogue")

    Returns:
        Dict with class data or None
    """
    return load_json_file("classes", index)


def load_equipment(index: str) -> Optional[Dict[str, Any]]:
    """
    Load equipment data from local JSON file.

    Args:
        index: Equipment index

    Returns:
        Dict with equipment data or None
    """
    return load_json_file("equipment", index)


def list_monsters() -> List[str]:
    """
    Get list of all available monsters from local files.

    Returns:
        List of monster indices
    """
    return list_json_files("monsters")


def list_spells() -> List[str]:
    """
    Get list of all available spells from local files.

    Returns:
        List of spell indices
    """
    return list_json_files("spells")


def list_equipment() -> List[str]:
    """
    Get list of all available equipment from local files.

    Returns:
        List of equipment indices
    """
    return list_json_files("equipment")


def list_weapons() -> List[str]:
    """
    Get list of all available weapons from local files.

    Returns:
        List of weapon indices
    """
    return list_json_files("weapons")


def list_armors() -> List[str]:
    """
    Get list of all available armors from local files.

    Returns:
        List of armor indices
    """
    return list_json_files("armors")


def list_races() -> List[str]:
    """
    Get list of all available races from local files.

    Returns:
        List of race indices
    """
    return list_json_files("races")


def list_classes() -> List[str]:
    """
    Get list of all available classes from local files.

    Returns:
        List of class indices
    """
    return list_json_files("classes")


def clear_cache():
    """
    Note: No cache needed when using local files.
    This function is kept for API compatibility.
    """
    print("No cache to clear (using local JSON files)")



# ===== Helper Functions =====

def parse_dice_notation(dice_str: str) -> tuple[int, int, int]:
    """
    Parse D&D dice notation.

    Args:
        dice_str: Dice string (e.g., "2d6+3", "1d8")

    Returns:
        Tuple of (dice_count, dice_sides, bonus)
    """
    import re

    # Match pattern like "2d6+3" or "1d8-2"
    match = re.match(r'(\d+)d(\d+)([+\-]\d+)?', dice_str)
    if match:
        dice_count = int(match.group(1))
        dice_sides = int(match.group(2))
        bonus = int(match.group(3)) if match.group(3) else 0
        return dice_count, dice_sides, bonus

    return 1, 6, 0  # Default


def parse_challenge_rating(cr_value: Any) -> float:
    """
    Parse challenge rating value.

    Args:
        cr_value: CR value (can be float, int, or fraction string)

    Returns:
        Float CR value
    """
    if isinstance(cr_value, (int, float)):
        return float(cr_value)

    if isinstance(cr_value, str):
        if '/' in cr_value:
            # Fraction like "1/2", "1/4"
            num, denom = cr_value.split('/')
            return float(num) / float(denom)
        return float(cr_value)

    return 0.0


# ===== Example Usage =====

if __name__ == "__main__":
    # Note: Data directory is auto-detected from dnd-5e-core/data
    # No need to call set_data_directory() unless you have a custom location

    # Example: Load goblin
    goblin_data = load_monster("goblin")
    if goblin_data:
        print(f"Loaded: {goblin_data.name}")
        print(f"CR: {goblin_data.challenge_rating}")
        print(f"HP: {goblin_data.hit_points}")

    # Example: List all monsters
    monsters = list_monsters()
    print(f"\nTotal monsters available: {len(monsters)}")
    print(f"First 5: {monsters[:5]}")

    # Example: Load fireball spell
    fireball_data = load_spell("fireball")
    if fireball_data:
        print(f"\nLoaded spell: {fireball_data.name}")
        print(f"Level: {fireball_data.level}")

