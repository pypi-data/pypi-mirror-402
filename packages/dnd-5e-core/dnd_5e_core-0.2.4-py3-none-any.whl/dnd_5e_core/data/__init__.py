"""
D&D 5e Core - Data Module
Data loading from local JSON files
"""

from .loader import (
    set_data_directory, get_data_directory,
    load_monster, load_spell, load_weapon, load_armor, load_magic_item,
    load_race, load_class, load_equipment,
    list_monsters, list_spells, list_equipment, list_weapons, list_armors,
    list_races, list_classes,
    clear_cache, parse_dice_notation, parse_challenge_rating
)

from .collections import (
    set_collections_directory, get_collections_directory,
    load_collection, populate, get_collection_count, get_collection_item,
    list_all_collections,
    get_monsters_list, get_spells_list, get_classes_list, get_races_list,
    get_equipment_list, get_weapons_list, get_armors_list, get_magic_items_list,
    # Object loading functions
    load_all_monsters, load_all_spells, load_all_weapons, load_all_armors,
    filter_monsters, filter_spells
)

__all__ = [
    # Data loader functions (individual objects)
    'set_data_directory', 'get_data_directory',
    'load_monster', 'load_spell', 'load_weapon', 'load_armor', 'load_magic_item',
    'load_race', 'load_class', 'load_equipment',
    'list_monsters', 'list_spells', 'list_equipment', 'list_weapons', 'list_armors',
    'list_races', 'list_classes',
    'clear_cache', 'parse_dice_notation', 'parse_challenge_rating',
    # Collections functions (indexes)
    'set_collections_directory', 'get_collections_directory',
    'load_collection', 'populate', 'get_collection_count', 'get_collection_item',
    'list_all_collections',
    'get_monsters_list', 'get_spells_list', 'get_classes_list', 'get_races_list',
    'get_equipment_list', 'get_weapons_list', 'get_armors_list', 'get_magic_items_list',
    # Object loading functions (bulk)
    'load_all_monsters', 'load_all_spells', 'load_all_weapons', 'load_all_armors',
    'filter_monsters', 'filter_spells'
]

