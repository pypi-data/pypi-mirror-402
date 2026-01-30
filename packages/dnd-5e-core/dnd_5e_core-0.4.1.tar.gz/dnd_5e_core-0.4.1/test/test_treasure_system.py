"""
Test script for improved treasure hoard system
Demonstrates treasure generation with magic items based on D&D 5e rules
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dnd_5e_core.mechanics.gold_rewards import (
    calculate_treasure_hoard,
    get_treasure_by_cr,
    get_tier_from_level,
    get_tier_from_cr,
)
from dnd_5e_core.equipment import get_magic_item, get_special_weapon, get_special_armor


def display_treasure(treasure: dict, title: str):
    """Display treasure in a formatted way"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

    print(f"\n💰 Gold: {treasure['gold']:,} gp")
    print(f"📊 Tier: {treasure['tier']}")
    print(f"💎 Estimated Total Value: {treasure['total_value_gp']:,} gp")

    if treasure['items']:
        print(f"\n✨ Magic Items ({len(treasure['items'])} items):")
        for i, item_index in enumerate(treasure['items'], 1):
            # Try to load the item
            item = None
            item = get_magic_item(item_index)
            if not item:
                item = get_special_weapon(item_index)
            if not item:
                item = get_special_armor(item_index)

            if item:
                rarity = item.rarity.value if hasattr(item, 'rarity') else 'unknown'
                cost = item.cost.quantity if hasattr(item, 'cost') else 0
                print(f"   {i}. {item.name:40} [{rarity:12}] ~{cost:>7,} gp")
            else:
                print(f"   {i}. {item_index:40} [unknown item]")
    else:
        print("\n✨ Magic Items: None")


def test_basic_treasure():
    """Test basic treasure generation at different levels"""
    print("\n" + "="*80)
    print("TEST 1: BASIC TREASURE BY LEVEL")
    print("="*80)

    test_levels = [1, 5, 10, 15, 20]

    for level in test_levels:
        tier = get_tier_from_level(level)
        treasure = calculate_treasure_hoard(level)
        print(f"\nLevel {level:2} ({tier}): {treasure['gold']:>7,} gp, "
              f"{len(treasure['items'])} items, "
              f"total ~{treasure['total_value_gp']:,} gp")


def test_difficulty_multipliers():
    """Test treasure with difficulty multipliers"""
    print("\n" + "="*80)
    print("TEST 2: DIFFICULTY MULTIPLIERS (Level 10)")
    print("="*80)

    difficulties = {
        'Easy': 0.5,
        'Medium': 1.0,
        'Hard': 1.5,
        'Deadly': 2.0,
    }

    for name, mult in difficulties.items():
        treasure = calculate_treasure_hoard(level=10, multiplier=mult)
        print(f"\n{name:8} (x{mult}): {treasure['gold']:>7,} gp, "
              f"{len(treasure['items'])} items")


def test_with_proficiencies():
    """Test treasure generation with party proficiencies"""
    print("\n" + "="*80)
    print("TEST 3: TREASURE WITH PARTY PROFICIENCIES")
    print("="*80)

    # Party with diverse proficiencies
    party_profs = [
        'Simple weapons',
        'Martial weapons',
        'Light armor',
        'Medium armor',
        'Heavy armor',
        'Shields',
    ]

    print("\n📋 Party Proficiencies:")
    for prof in party_profs:
        print(f"   - {prof}")

    treasure = calculate_treasure_hoard(
        level=10,
        multiplier=1.5,
        party_proficiencies=party_profs
    )

    display_treasure(treasure, "Level 10 Hard Encounter (with proficiencies)")


def test_by_challenge_rating():
    """Test treasure by Challenge Rating"""
    print("\n" + "="*80)
    print("TEST 4: TREASURE BY CHALLENGE RATING")
    print("="*80)

    test_crs = [0.5, 3, 7, 13, 20]

    for cr in test_crs:
        tier = get_tier_from_cr(cr)
        treasure = get_treasure_by_cr(cr)
        print(f"\nCR {cr:4} ({tier}): {treasure['gold']:>7,} gp, "
              f"{len(treasure['items'])} items")


def test_detailed_examples():
    """Test detailed treasure examples"""
    print("\n" + "="*80)
    print("TEST 5: DETAILED TREASURE EXAMPLES")
    print("="*80)

    # Example 1: Low-level encounter
    print("\n📖 Example 1: Party of 4 level-3 characters defeats goblin boss (CR 1)")
    treasure1 = get_treasure_by_cr(
        cr=1.0,
        party_proficiencies=['Simple weapons', 'Light armor']
    )
    display_treasure(treasure1, "Goblin Boss Treasure")

    # Example 2: Mid-level encounter
    print("\n📖 Example 2: Party of 5 level-8 characters defeats young dragon (CR 9)")
    treasure2 = calculate_treasure_hoard(
        level=8,
        multiplier=2.0,  # Deadly encounter
        cr=9,
        party_proficiencies=['Martial weapons', 'Heavy armor', 'Shields']
    )
    display_treasure(treasure2, "Young Dragon Hoard")

    # Example 3: High-level encounter
    print("\n📖 Example 3: Party of 6 level-15 characters defeats ancient dragon (CR 20)")
    treasure3 = calculate_treasure_hoard(
        level=15,
        multiplier=2.0,
        cr=20,
        party_proficiencies=['Martial weapons', 'Heavy armor', 'Medium armor', 'Light armor']
    )
    display_treasure(treasure3, "Ancient Dragon Hoard")


def test_multiple_hoards():
    """Generate multiple hoards to show variety"""
    print("\n" + "="*80)
    print("TEST 6: TREASURE VARIETY (5 level-10 medium encounters)")
    print("="*80)

    for i in range(5):
        treasure = calculate_treasure_hoard(level=10, multiplier=1.0)
        print(f"\nHoard {i+1}: {treasure['gold']:>7,} gp, {len(treasure['items'])} items", end="")
        if treasure['items']:
            print(f" - {', '.join([idx.split('-')[0] for idx in treasure['items'][:3]])}", end="")
            if len(treasure['items']) > 3:
                print(f"... (+{len(treasure['items'])-3} more)")
            else:
                print()
        else:
            print()


def test_no_items():
    """Test treasure without magic items"""
    print("\n" + "="*80)
    print("TEST 7: GOLD ONLY (no magic items)")
    print("="*80)

    treasure = calculate_treasure_hoard(level=10, include_items=False)
    display_treasure(treasure, "Gold-Only Treasure")


def main():
    """Run all tests"""
    print("="*80)
    print("D&D 5E TREASURE HOARD SYSTEM - COMPREHENSIVE TESTS")
    print("="*80)

    test_basic_treasure()
    test_difficulty_multipliers()
    test_with_proficiencies()
    test_by_challenge_rating()
    test_detailed_examples()
    test_multiple_hoards()
    test_no_items()

    print("\n" + "="*80)
    print("✅ ALL TESTS COMPLETED")
    print("="*80)
    print("\n💡 The treasure system now includes:")
    print("   - Gold based on encounter level/CR")
    print("   - Magic items based on D&D 5e treasure tables")
    print("   - Tier-appropriate item rarities")
    print("   - Party proficiency consideration")
    print("   - Difficulty multipliers")
    print("   - Variance for realism")
    print("\n📚 See gold_rewards.py for full API documentation")


if __name__ == "__main__":
    main()
