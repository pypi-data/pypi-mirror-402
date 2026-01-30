#!/usr/bin/env python3
"""
Test de chargement et combat avec monstres enrichis

Teste:
1. Chargement monstre officiel (format API)
2. Chargement monstre extended (format 5e.tools + parsing)
3. Combat entre les deux
"""
import json
import sys
from pathlib import Path

# Ajouter le chemin du package
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from dnd_5e_core.entities import Monster
from dnd_5e_core.data.loaders import load_monster
from dnd_5e_core.combat.combat_system import CombatSystem


def test_load_official_monster():
    """Test chargement monstre officiel"""
    print("=" * 80)
    print("🧪 TEST 1: CHARGEMENT MONSTRE OFFICIEL")
    print("=" * 80)
    print()

    try:
        # Charger avec la fonction load_monster
        goblin = load_monster('goblin')

        if goblin:
            print(f"✅ Monstre chargé: {goblin.name}")
            print(f"   HP: {goblin.current_hp}/{goblin.hit_points}")
            print(f"   AC: {goblin.armor_class}")
            print(f"   Actions: {len(goblin.actions) if goblin.actions else 0}")

            if goblin.actions:
                for action in goblin.actions[:3]:
                    print(f"     • {action.name}")
                    if hasattr(action, 'attack_bonus'):
                        print(f"       Bonus: +{action.attack_bonus}")
                    if hasattr(action, 'damages'):
                        for dmg in action.damages[:1]:
                            print(f"       Damage: {dmg.dice_count}d{dmg.dice_type}+{dmg.bonus}")

            return goblin
        else:
            print("❌ Échec chargement")
            return None

    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_load_extended_monster():
    """Test chargement monstre extended avec parsing"""
    print()
    print("=" * 80)
    print("🧪 TEST 2: CHARGEMENT MONSTRE EXTENDED (AVEC PARSING)")
    print("=" * 80)
    print()

    try:
        # Utiliser improved_converter pour charger et parser
        from improved_converter import ImprovedMonsterConverter

        # Trouver un monstre extended
        extended_dir = Path(__file__).parent
        json_files = [f for f in extended_dir.glob('*.json')
                     if f.name not in ['bestiary-sublist-data.json',
                                      'bestiary-sublist-data-all-monsters.json',
                                      'bestiary-sublist-data_ori.json']]

        if not json_files:
            print("❌ Aucun monstre extended trouvé")
            return None

        # Prendre le premier
        test_file = json_files[0]
        print(f"📖 Fichier: {test_file.name}")

        with open(test_file, 'r', encoding='utf-8') as f:
            monster_data = json.load(f)

        print(f"✅ Données chargées: {monster_data.get('name')}")

        # Convertir avec notre parser
        converter = ImprovedMonsterConverter()
        enriched = converter.convert_monster(monster_data)

        print(f"\n📊 Données parsées:")
        print(f"   Actions parsées: {len(enriched.get('actions_parsed', []))}")

        for action in enriched.get('actions_parsed', [])[:3]:
            print(f"     • {action['name']}")
            if action.get('attack_bonus'):
                print(f"       Bonus: +{action['attack_bonus']}")
            if action.get('damages'):
                for dmg in action['damages'][:1]:
                    print(f"       Damage: {dmg['formula']}")

        # Essayer de créer un Monster depuis ces données
        # Note: Il faudra adapter Monster class pour accepter le format enrichi
        print(f"\n⚠️  Création Monster depuis données enrichies nécessite adaptation de Monster class")

        return enriched

    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_combat():
    """Test combat entre monstres"""
    print()
    print("=" * 80)
    print("🧪 TEST 3: COMBAT DE TEST")
    print("=" * 80)
    print()

    try:
        # Charger deux gobelins pour le combat
        goblin1 = load_monster('goblin')
        goblin2 = load_monster('goblin')

        if not goblin1 or not goblin2:
            print("❌ Impossible de charger les monstres pour le combat")
            return

        goblin1.name = "Goblin 1"
        goblin2.name = "Goblin 2"

        print(f"⚔️  Combat: {goblin1.name} vs {goblin2.name}")
        print()

        # Créer système de combat
        combat = CombatSystem()

        # Tour 1
        print("🎲 Tour 1:")
        print(f"  {goblin1.name}: {goblin1.current_hp} HP")
        print(f"  {goblin2.name}: {goblin2.current_hp} HP")
        print()

        # Goblin 1 attaque Goblin 2
        if goblin1.actions:
            action = goblin1.actions[0]
            print(f"  {goblin1.name} utilise {action.name}")

            # Simuler attaque (simplifié)
            import random
            attack_roll = random.randint(1, 20)
            attack_bonus = getattr(action, 'attack_bonus', 0)
            total = attack_roll + attack_bonus

            print(f"    Jet d'attaque: {attack_roll} + {attack_bonus} = {total}")

            if total >= goblin2.armor_class:
                print(f"    ✅ Touche!")

                # Calculer dégâts
                if hasattr(action, 'damages') and action.damages:
                    dmg = action.damages[0]
                    damage_roll = sum(random.randint(1, dmg.dice_type) for _ in range(dmg.dice_count))
                    total_damage = damage_roll + dmg.bonus

                    print(f"    Dégâts: {damage_roll} + {dmg.bonus} = {total_damage}")

                    goblin2.current_hp -= total_damage
                    print(f"    {goblin2.name}: {goblin2.current_hp} HP")
            else:
                print(f"    ❌ Raté! (AC: {goblin2.armor_class})")

        print()

        if goblin2.current_hp > 0:
            print(f"✅ {goblin2.name} survit!")
        else:
            print(f"💀 {goblin2.name} est vaincu!")

        print()
        print("✅ Test de combat terminé")

    except Exception as e:
        print(f"❌ Erreur combat: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Point d'entrée principal"""
    print("=" * 80)
    print("🧪 TESTS DE CHARGEMENT ET COMBAT MONSTRES")
    print("=" * 80)
    print()

    # Test 1: Monstre officiel
    official_monster = test_load_official_monster()

    # Test 2: Monstre extended
    extended_monster = test_load_extended_monster()

    # Test 3: Combat
    if official_monster:
        test_combat()

    print()
    print("=" * 80)
    print("✅ TOUS LES TESTS TERMINÉS")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    exit(main())
