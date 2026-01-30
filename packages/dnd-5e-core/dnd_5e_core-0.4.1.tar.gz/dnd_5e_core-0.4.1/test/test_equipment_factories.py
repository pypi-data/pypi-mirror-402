"""
Test script for new armor, weapon, and magic item factories
"""
import sys
from pathlib import Path

# Add parent directory to path to use local development version
sys.path.insert(0, str(Path(__file__).parent.parent))

from dnd_5e_core.equipment import (
    # Armor
    create_armor_of_invulnerability,
    create_dragon_scale_mail,
    create_dwarven_plate,
    create_elven_chain,
    create_mithral_armor,
    create_adamantine_armor,
    create_animated_shield,
    get_special_armor,

    # Weapons
    create_flame_tongue,
    create_frost_brand,
    create_holy_avenger,
    create_vorpal_sword,
    create_sun_blade,
    get_special_weapon,

    # Magic Items
    create_potion_of_healing,
    create_potion_of_greater_healing,
    create_antitoxin,
    create_elixir_of_health,
    create_ring_of_protection,
    create_belt_of_giant_strength,
    create_wand_of_magic_missiles,
    create_staff_of_healing,
    get_magic_item,
    MAGIC_ITEMS_REGISTRY,
)


def test_armors():
    """Test special armor creation"""
    print("=" * 80)
    print("TESTING SPECIAL ARMORS")
    print("=" * 80)

    print("\n1. Armor of Invulnerability:")
    armor = create_armor_of_invulnerability()
    print(f"   {armor.name} - AC: {armor.armor_class['base']}, Cost: {armor.cost.quantity}gp")

    print("\n2. Red Dragon Scale Mail:")
    armor = create_dragon_scale_mail("red")
    print(f"   {armor.name} - AC: {armor.armor_class['base']}, Cost: {armor.cost.quantity}gp")

    print("\n3. Dwarven Plate:")
    armor = create_dwarven_plate()
    print(f"   {armor.name} - AC: {armor.armor_class['base']}, Cost: {armor.cost.quantity}gp")

    print("\n4. Elven Chain:")
    armor = create_elven_chain()
    print(f"   {armor.name} - AC: {armor.armor_class['base']}, No stealth disadvantage")

    print("\n5. Mithral Plate:")
    armor = create_mithral_armor("plate")
    print(f"   {armor.name} - No stealth disadvantage, no STR requirement")

    print("\n6. Adamantine Chain Mail:")
    armor = create_adamantine_armor("chain-mail")
    print(f"   {armor.name} - Critical hits become normal hits")

    print("\n7. Animated Shield:")
    shield = create_animated_shield()
    print(f"   {shield.name} - Can float and grant AC without using hands")

    print("\n8. Using get_special_armor:")
    armor = get_special_armor("dwarven-plate")
    if armor:
        print(f"   Retrieved: {armor.name}")


def test_weapons():
    """Test special weapon creation"""
    print("\n" + "=" * 80)
    print("TESTING SPECIAL WEAPONS")
    print("=" * 80)

    print("\n1. Flame Tongue:")
    weapon = create_flame_tongue()
    print(f"   {weapon.name} - Damage: {weapon.damage_dice}, +2d6 fire when ignited")

    print("\n2. Frost Brand:")
    weapon = create_frost_brand()
    print(f"   {weapon.name} - Damage: {weapon.damage_dice}, +1d6 cold, fire resistance")

    print("\n3. Holy Avenger:")
    weapon = create_holy_avenger()
    print(f"   {weapon.name} - +3, +2d10 radiant vs fiends/undead, Cost: {weapon.cost.quantity}gp")

    print("\n4. Vorpal Sword:")
    weapon = create_vorpal_sword()
    print(f"   {weapon.name} - +3, can decapitate on critical hit")

    print("\n5. Sun Blade:")
    weapon = create_sun_blade()
    print(f"   {weapon.name} - +2, finesse, radiant damage, emits sunlight")

    print("\n6. Oathbow:")
    weapon = get_special_weapon("oathbow")
    if weapon:
        print(f"   {weapon.name} - +3d6 vs sworn enemy, advantage on attacks")


def test_magic_items():
    """Test magic items and potions"""
    print("\n" + "=" * 80)
    print("TESTING MAGIC ITEMS & POTIONS")
    print("=" * 80)

    print("\n1. Potion of Healing:")
    potion = create_potion_of_healing()
    print(f"   {potion.name} - Restores 2d4+2 HP, Cost: {potion.cost.quantity}gp")

    print("\n2. Potion of Greater Healing:")
    potion = create_potion_of_greater_healing()
    print(f"   {potion.name} - Restores 4d4+4 HP, Cost: {potion.cost.quantity}gp")

    print("\n3. Antitoxin:")
    antitoxin = create_antitoxin()
    print(f"   {antitoxin.name} - Advantage on poison saves for 1 hour")

    print("\n4. Elixir of Health:")
    elixir = create_elixir_of_health()
    print(f"   {elixir.name} - Cures diseases and conditions, Cost: {elixir.cost.quantity}gp")

    print("\n5. Ring of Protection:")
    ring = create_ring_of_protection()
    print(f"   {ring.name} - +1 AC and saves, Requires attunement: {ring.requires_attunement}")

    print("\n6. Belt of Hill Giant Strength:")
    belt = create_belt_of_giant_strength("hill")
    print(f"   {belt.name} - STR becomes 21, Cost: {belt.cost.quantity}gp")

    print("\n7. Wand of Magic Missiles:")
    wand = create_wand_of_magic_missiles()
    print(f"   {wand.name} - {len(wand.actions)} action(s), {wand.actions[0].uses_per_day} charges")

    print("\n8. Staff of Healing:")
    staff = create_staff_of_healing()
    print(f"   {staff.name} - {staff.actions[0].name}: {staff.actions[0].healing_dice}")

    print("\n9. Using get_magic_item:")
    item = get_magic_item("ring-of-protection")
    if item:
        print(f"   Retrieved: {item.name}")


def test_registry():
    """Test the magic items registry"""
    print("\n" + "=" * 80)
    print("MAGIC ITEMS REGISTRY")
    print("=" * 80)

    print(f"\nTotal magic items in registry: {len(MAGIC_ITEMS_REGISTRY)}")

    print("\nSample items:")
    for i, (key, factory) in enumerate(list(MAGIC_ITEMS_REGISTRY.items())[:10]):
        item = factory()
        print(f"   {i+1}. {key}: {item.name} ({item.rarity.value})")

    print("\n   ... and {} more".format(len(MAGIC_ITEMS_REGISTRY) - 10))


def main():
    """Run all tests"""
    test_armors()
    test_weapons()
    test_magic_items()
    test_registry()

    print("\n" + "=" * 80)
    print("✅ ALL TESTS COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    main()
