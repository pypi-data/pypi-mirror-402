# dnd-5e-core

## 📖 About

**Complete D&D 5th Edition Rules Engine** - A comprehensive Python package implementing all core D&D 5e mechanics and official rules. UI-agnostic design works with any interface (pygame, web, CLI, Qt). Includes 8.7MB of bundled JSON data (2000+ files) with 332 monsters, 319 spells, and complete game rules. **100% standalone** - no external APIs required, works offline!

[![PyPI version](https://badge.fury.io/py/dnd-5e-core.svg)](https://pypi.org/project/dnd-5e-core/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A complete Python package implementing D&D 5th Edition core rules and mechanics, including **official encounter system**, **gold rewards**, **experience tables**, and **standalone character/monster loaders**.

This package contains **all game logic** for D&D 5e and is **UI-agnostic** - use it with pygame, ncurses, web, Qt, or any other interface.

## 🎮 Examples & Frontends

**Looking for examples or complete applications?**

- **[DnD5e-Test](https://github.com/codingame-team/DND5e-Test)** - Demonstration scripts and examples
  - 10+ combat scripts with random character generation
  - Official D&D 5e encounter builder examples
  - Character and monster creation demos
  - All scripts work standalone with just `pip install dnd-5e-core`

- **[DnD-5th-Edition-API](https://github.com/codingame-team/DnD-5th-Edition-API)** - Complete applications
  - Full-featured ncurses interface (terminal-based)
  - Pygame dungeon crawler with real-time combat
  - PyQt5 Wizardry-style interface
  - Character management, inventory, shops, and more

## ✨ New in Version 0.2.5 (January 2026)

**🎓 Complete Class Progression System**:
- **Automatic spell slots** based on official API data for all caster classes
- **Level-up system** with automatic HP, features, and spell slot progression
- **Class-specific features** (Barbarian rage, Monk ki, Rogue sneak attack, etc.)
- **20 levels of progression** for all 12 classes
- Seamlessly integrated into `simple_character_generator()`

```python
# Spell slots are now automatically correct!
wizard = simple_character_generator(5, 'elf', 'wizard', 'Gandalf')
print(wizard.sc.spell_slots)  # [0, 4, 3, 2, 0, ...] ✅ Correct for level 5!

# Automatic level up with all benefits
wizard = level_up_character(wizard, 6)
# Applies: HP gain, spell slots update, new features, etc.
```

**🎯 Subclasses & Subraces System** ✨ NEW:
- **Subclasses** for all classes (School of Evocation, Champion, Life Domain, etc.)
- **Subraces** for all races (High Elf, Hill Dwarf, Lightfoot Halfling, etc.)
- Load from official D&D 5e API data

```python
from dnd_5e_core.mechanics.subclass_system import load_subclass, load_subrace

# Load a subclass
champion = load_subclass('champion')  # Fighter subclass
print(f"{champion.name}: {champion.subclass_flavor}")

# Load a subrace
high_elf = load_subrace('high-elf')
print(f"{high_elf.name}: +{high_elf.ability_bonuses}")
```

**⚔️ Multiclassing System** ✨ NEW:
- Full support for multiclass characters
- Automatic spell slot calculation for multiclass casters
- Track levels in multiple classes

```python
from dnd_5e_core.mechanics.subclass_system import MulticlassCharacter

# Create a Fighter 5 / Wizard 3
gish = MulticlassCharacter("Elric")
for _ in range(5):
    gish.add_class_level('fighter')
for _ in range(3):
    gish.add_class_level('wizard')

print(f"{gish}")  # "Fighter 5 / Wizard 3"
print(f"Total level: {gish.get_total_level()}")  # 8
print(f"Spell slots: {gish.get_spell_slots_multiclass()}")  # Calculated correctly!
```

## ✨ New in Version 0.1.8

**📝 Enhanced PyPI Documentation**:
- Updated description highlighting all v0.1.7 features
- Added links to example projects and full applications
- Better showcasing of standalone capabilities

**🎯 All Features from v0.1.7** (fully documented):
- **Gold Rewards System**: Official treasure tables from DMG (levels 1-20)
- **Encounter Builder**: DMG-compliant encounter generation with balanced difficulty
- **Standalone Loaders**: Character and monster loading without external dependencies
- **All D&D 5e Rules**: 100% of core mechanics in the package

**🎮 Integrated D&D 5e Data**: The package includes **8.7 MB of D&D 5e JSON data** (2000+ files):
- **332 monsters** with complete stats and abilities
- **319 spells** with full descriptions and mechanics
- **65 weapons** with damage, properties, and ranges
- **30 armors** with AC calculations
- **237 equipment items**
- Plus: races, classes, traits, features, and more!

**🐉 Extended Monsters from 5e.tools**: Access to **89+ additional monsters**:
- Monsters not in the official API (Orc Eye of Gruumsh, Goblin Boss, etc.)
- 47 monsters with complete actions and abilities implemented
- Support for downloading monster tokens/images
- Advanced search and filtering capabilities

**📦 100% Standalone** - No external API or database required - all data is bundled and **auto-detected**.

## 💥 Combat Examples

**📖 [Complete Combat Examples Guide](./COMBAT_EXAMPLES.md)** - Detailed examples with full code and explanations

### Complete Combat with Spellcasting and Equipment

The `CombatSystem` automatically handles spells, special attacks, healing, and weapon attacks. Here's a complete example:

```python
from dnd_5e_core import load_monster
from dnd_5e_core.data.loaders import simple_character_generator
from dnd_5e_core.data import load_weapon, load_armor
from dnd_5e_core.combat import CombatSystem

# Create a wizard
wizard = simple_character_generator(level=5, race_name='elf', class_name='wizard', name='Gandalf')

# Create fighters for front row
fighter1 = simple_character_generator(level=5, class_name='fighter', name='Conan')
fighter2 = simple_character_generator(level=5, class_name='fighter', name='Aragorn')
fighter3 = simple_character_generator(level=5, class_name='fighter', name='Beorn')

# Equip fighters with weapons and armor
longsword = load_weapon("longsword")
battleaxe = load_weapon("battleaxe")
greatsword = load_weapon("greatsword")

chain_mail = load_armor("chain-mail")
scale_mail = load_armor("scale-mail")
ring_mail = load_armor("ring-mail")

# Equip Fighter 1
if fighter1.inventory and longsword:
    for i, item in enumerate(fighter1.inventory):
        if item is None:
            fighter1.inventory[i] = longsword
            break
    fighter1.equip(longsword)
    
if fighter1.inventory and chain_mail:
    for i, item in enumerate(fighter1.inventory):
        if item is None:
            fighter1.inventory[i] = chain_mail
            break
    fighter1.equip(chain_mail)

# Equip Fighter 2 and 3 similarly...

# Load a monster
ogre = load_monster('ogre')

# Party formation: fighters in front (0-2), wizard in back (3) for spellcasting
# This is IMPORTANT: wizards must be in position 3+ to cast spells!
party = [fighter1, fighter2, fighter3, wizard]

print(f"⚔️ Party Formation:")
print(f"   Front Row (Melee): {fighter1.name}, {fighter2.name}, {fighter3.name}")
print(f"   Back Row (Spells): {wizard.name} 🔮")

# Start combat
combat = CombatSystem(verbose=True)
alive_chars = [c for c in party if c.hit_points > 0]
alive_monsters = [ogre]

round_num = 1
while alive_chars and alive_monsters and round_num <= 10:
    print(f"\n=== Round {round_num} ===")
    
    # Character turns
    for char in alive_chars[:]:
        if not alive_monsters:
            break
        if char.hit_points <= 0:
            if char in alive_chars:
                alive_chars.remove(char)
            continue
        
        combat.character_turn(
            character=char,
            alive_chars=alive_chars,
            alive_monsters=alive_monsters,
            party=party
        )
    
    # Monster turns
    for monster in alive_monsters[:]:
        if not alive_chars:
            break
        if monster.hit_points <= 0:
            if monster in alive_monsters:
                alive_monsters.remove(monster)
            continue
        
        combat.monster_turn(
            monster=monster,
            alive_monsters=alive_monsters,
            alive_chars=alive_chars,
            party=party,
            round_num=round_num
        )
    
    round_num += 1

# Results
if alive_chars:
    print(f"\n✅ VICTORY!")
    if hasattr(wizard, 'sc') and wizard.sc:
        print(f"\n{wizard.name}'s Spells Cast:")
        print(f"   Spell Slots Before: [4, 3, 2, 0, 0]")
        print(f"   Spell Slots After:  {wizard.sc.spell_slots[1:6]}")
```

**Output Example:**
```
⚔️ Party Formation:
   Front Row (Melee): Conan, Aragorn, Beorn
   Back Row (Spells): Gandalf 🔮

=== Round 1 ===
Conan attacks Ogre!
Conan slashes Ogre for 5 hit points!
Aragorn attacks Ogre!
Aragorn slashes Ogre for 6 hit points!
Beorn attacks Ogre!
Beorn slashes Ogre for 10 hit points!
Gandalf attacks Ogre!
Gandalf CAST SPELL ** ICE STORM ** on Ogre
Ogre is hit for 18 hit points!
Ogre bludgeones Conan for 12 hit points!

✅ VICTORY!
Gandalf's Spells Cast: 3 spells used
```

### Key Combat Features Demonstrated

1. **🔮 Character Spellcasting**: 
   - Wizards automatically cast spells when in back row (position 3+)
   - Spell slots are tracked and consumed
   - Cantrips and leveled spells both work
   
2. **👹 Monster Spellcasting**:
   ```python
   mage = load_monster('mage')  # Spellcasting monster
   # Mage will automatically cast spells like Cone of Cold, Ice Storm
   ```

3. **⚔️ Equipped Weapons**:
   - Characters use equipped weapons ("slashes" vs "punches")
   - Damage dice rolled automatically
   - AC from armor properly calculated

4. **🎯 Special Attacks**:
   ```python
   dragon = load_monster('young-red-dragon')
   # Dragon uses multi-attack and breath weapon automatically
   ```

5. **🩹 Automatic Healing**:
   - Characters with healing spells heal wounded allies
   - Potions are used when HP is low
   
6. **📊 Combat Intelligence**:
   - `CombatSystem` handles all tactical decisions
   - Priority: Heal → Potions → Spells → Special Attacks → Weapons

### Spellcaster vs Spellcaster Combat

```python
# Create two wizards
wizard1 = simple_character_generator(level=5, class_name='wizard', name='Gandalf')
wizard2 = simple_character_generator(level=5, class_name='wizard', name='Saruman')

# Show their spells
print(f"{wizard1.name}'s Spells:")
for spell in wizard1.sc.learned_spells[:5]:
    print(f"  - {spell.name} (Level {spell.level})")

# Add front-row guards so wizards are in ranged position
party1 = [guard1, guard2, guard3, wizard1]
party2 = [guard4, guard5, guard6, wizard2]

# Combat proceeds with spell-vs-spell battles!
```

### Monster Special Attacks

```python
# Load a monster with special abilities
dragon = load_monster('young-red-dragon')

if hasattr(dragon, 'sa') and dragon.sa:
    print(f"Special Attacks: {[sa.name for sa in dragon.sa]}")
    # Output: Multi-attack, Breath Weapon

# During combat, dragon will automatically use these
# combat.monster_turn() handles special attack logic
```

### Party Formation Tips

**⚠️ Important for Spellcasting:**

Characters in positions **0-2** are considered **melee** (front row)
Characters in positions **3+** are considered **ranged** (back row)

**Wizards and other spellcasters MUST be in positions 3+ to cast spells!**

```python
# ✅ CORRECT - Wizard will cast spells
party = [fighter1, fighter2, fighter3, wizard]  # wizard at position 3

# ❌ WRONG - Wizard will only use weapon
party = [wizard]  # wizard at position 0 (melee)
```

## Features

### Complete D&D 5e Implementation

**Core Mechanics:**
- **Entities**: Monster and Character classes with full D&D 5e mechanics
- **Races & Subraces**: All official races with ability bonuses, traits, proficiencies
- **Classes**: All character classes with spellcasting, proficiencies
- **Equipment**: Weapons (with properties, ranges), Armor (AC calculation), Potions
- **Spells**: Complete spellcasting system with spell slots, cantrips, DC
- **Combat**: Actions, Multi-attacks, Special Abilities, Conditions
- **Abilities**: Six core abilities (STR, DEX, CON, INT, WIS, CHA) with modifiers
- **Saving Throws**: Full saving throw system with proficiencies

**Official D&D 5e Rules (NEW in v0.1.7):**
- **📊 Encounter Tables**: Official DMG encounter tables (levels 1-20)
- **💰 Gold Rewards**: Treasure per encounter from DMG
- **⚔️ Challenge Rating**: Accurate encounter difficulty calculation
- **📈 Experience System**: XP tables and level progression
- **🎲 Encounter Builder**: Generate balanced encounters by party level

**Standalone Utilities (NEW in v0.1.7):**
- **Character Generator**: Create random characters without external dependencies
- **Monster Loader**: Load monsters from bundled data or API
- **Data Collections**: Access all D&D 5e data easily

### Integrated Data

- **✅ Bundled JSON Data**: 2000+ D&D 5e data files included (8.7 MB)
- **✅ Auto-Detection**: No configuration needed - data is found automatically
- **✅ Offline Mode**: Works without internet connection
- **✅ Complete**: Monsters, spells, weapons, armors, classes, races, and more
- **✅ Extended**: 89+ additional monsters from 5e.tools

## 📚 Documentation

**Complete API Documentation Available!**

- **[API Documentation Index](./docs/api/README.md)** - Start here for complete package documentation
- **[Quick Reference](./docs/api/INDEX.md)** - Overview of all modules and features

### Module Documentation
- [entities](./docs/api/entities.md) - Characters and monsters
- [combat](./docs/api/combat.md) - Combat system
- [mechanics](./docs/api/mechanics.md) - Game rules and dice
- [equipment](./docs/api/equipment.md) - Weapons, armor, potions
- [spells](./docs/api/spells.md) - Magic system
- [data](./docs/api/data.md) - Data loading and serialization
- [races-classes-abilities](./docs/api/races-classes-abilities.md) - Character customization
- [ui-utils](./docs/api/ui-utils.md) - UI helpers and utilities

## Installation

```bash
pip install dnd-5e-core
```

Or for development:

```bash
git clone https://github.com/codingame-team/dnd-5e-core.git
cd dnd-5e-core
pip install -e .[dev]
```

## Quick Start

### NEW in v0.1.7: Standalone Character & Monster Loaders

```python
from dnd_5e_core.data import simple_character_generator, load_monsters_database

# Generate random characters without external dependencies
fighter = simple_character_generator(level=5, class_name="fighter", name="Conan")
wizard = simple_character_generator(level=5, class_name="wizard")

print(f"{fighter.name} - Level {fighter.level} {fighter.class_type.name}")
print(f"HP: {fighter.hit_points}/{fighter.max_hit_points}")

# Load all monsters at once
monsters = load_monsters_database()
print(f"Loaded {len(monsters)} monsters")
```

### NEW in v0.1.7: Official D&D 5e Encounter System

```python
from dnd_5e_core.mechanics import (
    select_monsters_by_encounter_table,
    get_encounter_gold,
    ENCOUNTER_TABLE,
    XP_LEVELS
)

# Generate balanced encounter for a level 5 party
party_levels = [5, 5, 4, 6]
monsters, encounter_type = select_monsters_by_encounter_table(
    encounter_level=5,
    available_monsters=monsters_db,
    allow_pairs=True
)

print(f"Encounter: {encounter_type}")
print(f"Monsters: {[m.name for m in monsters]}")

# Get gold reward
gold = get_encounter_gold(5)
print(f"Treasure: {gold} gp")

# Check XP table
xp_for_level_5 = XP_LEVELS[5]
print(f"XP needed for level 5: {xp_for_level_5}")
```

### Load D&D 5e Data

```python
from dnd_5e_core.data import load_monster, list_monsters, load_spell

# List all available monsters
monsters = list_monsters()
print(f"Total monsters: {len(monsters)}")  # 332

# Load a specific monster
goblin = load_monster('goblin')
print(f"Name: {goblin['name']}")
print(f"HP: {goblin['hit_points']}")
print(f"CR: {goblin['challenge_rating']}")

# Load a spell
fireball = load_spell('fireball')
print(f"Spell: {fireball['name']}, Level: {fireball['level']}")
```

**Note**: Data directory is **auto-detected** - no configuration needed!

### Create a Character

```python
from dnd_5e_core.entities import Character
from dnd_5e_core.races import Race
from dnd_5e_core.classes import ClassType
from dnd_5e_core.abilities import Abilities

# Load race and class from API
race = Race.load_from_api("elf")
class_type = ClassType.load_from_api("wizard")

# Create abilities
abilities = Abilities(
    strength=10,
    dexterity=14,
    constitution=12,
    intelligence=16,
    wisdom=13,
    charisma=8
)

# Create character
wizard = Character(
    name="Gandalf",
    race=race,
    class_type=class_type,
    abilities=abilities,
    level=1,
    hit_points=8,
    max_hit_points=8,
    gold=100
)

# Equip weapon
from dnd_5e_core.equipment import Weapon
staff = Weapon.load_from_api("quarterstaff")
wizard.inventory.append(staff)
staff.equipped = True

print(f"{wizard.name} - Level {wizard.level} {wizard.race.name} {wizard.class_type.name}")
print(f"AC: {wizard.armor_class}, HP: {wizard.hit_points}/{wizard.max_hit_points}")
```

### Create a Monster

```python
from dnd_5e_core.entities import Monster

# Load from API
orc = Monster.load_from_api("orc")

print(f"{orc.name} - CR {orc.challenge_rating}")
print(f"AC: {orc.armor_class}, HP: {orc.hit_points}")
print(f"Actions: {[a.name for a in orc.actions]}")
```

### Extended Monsters from 5e.tools (New!)

```python
from dnd_5e_core.entities import get_extended_monster_loader

# Load the monster loader
loader = get_extended_monster_loader()

# Search for monsters
goblins = loader.search_monsters(name_contains="goblin", min_cr=1, max_cr=3)
print(f"Found {len(goblins)} goblin variants")

# Get a specific monster with full data
orc_eye = loader.get_monster_by_name("Orc Eye of Gruumsh")
print(f"{orc_eye['name']} - CR {orc_eye['cr']}")
print(f"HP: {orc_eye['hp']['average']}, Source: {orc_eye['source']}")

# Get statistics
stats = loader.get_stats()
print(f"Total extended monsters: {stats['total']}")
print(f"Sources: {list(stats['by_source'].keys())}")

# Download monster tokens
from dnd_5e_core.utils import download_monster_token

download_monster_token("Orc Eye of Gruumsh", source="MM", save_folder="tokens")
```

### Combat System

**See the [Combat Examples](#-combat-examples) section above for complete working examples!**

The `CombatSystem` class handles all combat logic automatically:

```python
from dnd_5e_core.combat import CombatSystem

combat = CombatSystem(verbose=True)

# Characters automatically:
# - Cast spells if in ranged position (3+)
# - Use healing spells on wounded allies
# - Drink potions when low HP
# - Attack with equipped weapons

# Character turn
combat.character_turn(
    character=wizard,
    alive_chars=party,
    alive_monsters=[ogre],
    party=party
)

# Monster turn (handles spellcasting, special attacks, etc.)
combat.monster_turn(
    monster=ogre,
    alive_monsters=[ogre],
    alive_chars=party,
    party=party,
    round_num=1
)
```

**Combat Features:**
- ✅ Automatic spell casting for characters and monsters
- ✅ Special attacks (dragon breath, multi-attack, etc.)
- ✅ Healing spells and potions
- ✅ Weapon damage calculation
- ✅ Saving throws and DC checks
- ✅ Tactical decision making
```

### Spellcasting

```python
from dnd_5e_core.spells import Spell

# Character must have spellcasting ability
if wizard.is_spell_caster:
    # Load spell from API
    fireball = Spell.load_from_api("fireball")

    # Check if can cast
    if wizard.can_cast(fireball):
        # Cast spell at target
        damage = wizard.cast_attack(orc, fireball)
        print(f"{wizard.name} casts Fireball on {orc.name} for {damage} damage!")

        # Saving throw
        if orc.saving_throw(dc_type=fireball.dc_type, dc_value=wizard.dc_value):
            print(f"{orc.name} succeeded saving throw!")
```

## Architecture

This package follows **separation of concerns**:

### What this package DOES:
- All D&D 5e game rules and mechanics
- Character/Monster creation and management
- Combat resolution and damage calculation
- Spell casting and effects
- Equipment management
- Saving throws, ability checks
- Experience and leveling
- Data loading from D&D 5e API

### What this package DOES NOT do:
- User interface (no pygame, no ncurses, no GUI)
- Game loop management
- Graphics rendering
- Sound effects
- Input handling
- Save file management (provides serialization only)

### Your application provides:
- UI layer (console, GUI, web, etc.)
- Game state management
- User input handling
- Rendering and display
- Save/load game state using provided serialization

## Usage in Your Project

```python
# Your game imports dnd-5e-core for game logic
from dnd_5e_core.entities import Character, Monster
from dnd_5e_core.combat import CombatSystem

# You provide the UI
import pygame  # or curses, or tkinter, or web framework

# Game loop (you control this)
while running:
    # Handle input (your code)
    key = get_user_input()

    # Call game logic (dnd-5e-core)
    if key == "attack":
        damage = player.attack(monster)

    # Render (your code)
    render_game_state(player, monster)
```

## Data Sources

The package can load data from:
1. **D&D 5e API** (https://www.dnd5eapi.co/) - Default
2. **Local JSON files** - For offline mode
3. **Custom data** - Implement your own loader

## 📁 Project Structure

```
dnd-5e-core/
├── dnd_5e_core/          # Main package code
│   ├── abilities/        # Ability scores system
│   ├── classes/          # Character classes
│   ├── combat/           # Combat system
│   ├── data/             # Data loaders and collections
│   ├── entities/         # Characters, monsters, sprites
│   ├── equipment/        # Weapons, armor, items
│   ├── mechanics/        # Game mechanics (dice, CR, encounters)
│   ├── races/            # Character races
│   ├── spells/           # Spell system
│   └── ui/               # UI utilities (colors, display)
├── data/                 # Bundled D&D 5e JSON data (8.7 MB)
├── docs/                 # Complete API documentation
├── tests/                # Test suite and examples
│   ├── examples/         # Usage examples
│   └── test_*.py         # Unit tests
├── archive/              # Development history docs
├── README.md             # This file
├── CHANGELOG.md          # Version history
├── COMBAT_EXAMPLES.md    # Combat system examples
├── CONTRIBUTING.md       # Contribution guide
└── pyproject.toml        # Package configuration
```

## Testing

Run all tests:
```bash
pytest tests/
```

Run specific test:
```bash
pytest tests/test_spell_loading.py -v
```

Verify package installation:
```bash
python tests/verify_package.py
```

See **[tests/README.md](tests/README.md)** for details on all test scripts.

## Documentation

### Main Documentation
- **[README.md](README.md)** - This file (package overview)
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and changes
- **[COMBAT_EXAMPLES.md](COMBAT_EXAMPLES.md)** - Complete combat examples
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - How to contribute

### API Documentation
See **[docs/](docs/)** folder for detailed API documentation:
- Entity System (Characters, Monsters)
- Combat Mechanics
- Spellcasting System
- Equipment Guide
- Extended Monsters from 5e.tools
- Complete API Reference

### Development History
See **[archive/](archive/)** folder for historical development documents (not needed for usage)

## License

MIT License - See LICENSE file for details

## Contributing

See CONTRIBUTING.md for guidelines.

## Credits

Based on D&D 5th Edition rules © Wizards of the Coast.
This is a fan-made implementation for educational purposes.
