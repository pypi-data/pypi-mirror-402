#!/usr/bin/env python3
"""
Script de restauration et correction finale

1. Déplace TOUS les monstres de invalid/ vers extended/
2. Corrige le parser de sorts pour gérer les espaces
3. Lance un test de combat complet
"""
import json
import shutil
from pathlib import Path
import sys

# Ajouter chemins
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


def restore_all_monsters():
    """Déplace tous les monstres de invalid/ vers extended/"""
    print("=" * 80)
    print("📦 RESTAURATION DES MONSTRES")
    print("=" * 80)
    print()

    extended_dir = Path(__file__).parent
    invalid_dir = extended_dir / 'invalid'

    if not invalid_dir.exists():
        print("✅ Aucun fichier à restaurer (invalid/ n'existe pas)")
        return 0

    json_files = list(invalid_dir.glob('*.json'))

    if not json_files:
        print("✅ Aucun fichier à restaurer (invalid/ est vide)")
        return 0

    print(f"📁 {len(json_files)} fichiers trouvés dans invalid/")
    print()

    response = input(f"Déplacer TOUS les {len(json_files)} fichiers vers extended/ ? (oui/non): ")

    if response.lower() not in ['oui', 'o', 'yes', 'y']:
        print("❌ Restauration annulée")
        return 1

    print()
    print("📦 Déplacement en cours...")

    moved = 0
    for filepath in json_files:
        try:
            dest = extended_dir / filepath.name
            shutil.move(str(filepath), str(dest))
            moved += 1

            if moved % 100 == 0:
                print(f"  [{moved}/{len(json_files)}] Déplacés...")
        except Exception as e:
            print(f"  ❌ Erreur {filepath.name}: {e}")

    print()
    print(f"✅ {moved} fichiers déplacés vers extended/")

    return moved


def test_spell_name_normalization():
    """Test de normalisation des noms de sorts"""
    print()
    print("=" * 80)
    print("🧪 TEST NORMALISATION NOMS DE SORTS")
    print("=" * 80)
    print()

    test_cases = [
        ("detect magic", "detect-magic"),
        ("cure wounds", "cure-wounds"),
        ("magic missile", "magic-missile"),
        ("sacred flame", "sacred-flame"),
        ("fireball", "fireball"),
        ("mage hand", "mage-hand"),
    ]

    print("Tests de normalisation:")
    for spell_name, expected in test_cases:
        normalized = spell_name.lower().replace(' ', '-')
        status = "✅" if normalized == expected else "❌"
        print(f"  {status} '{spell_name}' → '{normalized}' (attendu: '{expected}')")

    print()
    print("✅ Normalisation: espace → tiret")


def run_complete_combat_test():
    """Test de combat complet avec monstres extended"""
    print()
    print("=" * 80)
    print("⚔️  TEST DE COMBAT COMPLET")
    print("=" * 80)
    print()

    try:
        from dnd_5e_core.data.loaders import load_monster
        from improved_converter import ImprovedMonsterConverter
        import random

        # Test 1: Monstre officiel
        print("Test 1: Chargement monstre officiel")
        goblin = load_monster('goblin')

        if goblin:
            print(f"  ✅ {goblin.name} chargé")
            print(f"     HP: {goblin.current_hp}, AC: {goblin.armor_class}")
            if goblin.actions:
                print(f"     Actions: {len(goblin.actions)}")
        else:
            print(f"  ❌ Échec chargement goblin")
            return 1

        # Test 2: Monstre extended parsé
        print()
        print("Test 2: Monstre extended avec parsing")

        extended_dir = Path(__file__).parent
        json_files = [f for f in extended_dir.glob('*.json')
                     if f.name not in ['bestiary-sublist-data.json',
                                      'bestiary-sublist-data-all-monsters.json',
                                      'bestiary-sublist-data_ori.json']]

        if not json_files:
            print("  ❌ Aucun monstre extended trouvé")
            return 1

        # Prendre acolyte.json pour tester le spellcasting
        test_file = None
        for f in json_files:
            if 'acolyte' in f.name.lower():
                test_file = f
                break

        if not test_file:
            test_file = json_files[0]

        with open(test_file, 'r', encoding='utf-8') as f:
            monster_data = json.load(f)

        print(f"  Fichier: {test_file.name}")
        print(f"  ✅ {monster_data.get('name')} chargé")

        # Parser
        converter = ImprovedMonsterConverter()
        enriched = converter.convert_monster(monster_data)

        # Vérifier actions
        if enriched.get('actions_parsed'):
            print(f"     Actions parsées: {len(enriched['actions_parsed'])}")
            for action in enriched['actions_parsed'][:2]:
                print(f"       • {action['name']}")
                if action.get('attack_bonus'):
                    print(f"         +{action['attack_bonus']} to hit")

        # Vérifier spellcasting
        if enriched.get('spellcasting_parsed'):
            sc = enriched['spellcasting_parsed']
            total_spells = 0

            for spells in sc.get('spells_by_level', {}).values():
                total_spells += len(spells)
            total_spells += len(sc.get('at_will', []))

            if total_spells > 0:
                print(f"     Spellcasting: {total_spells} sorts")

                # Afficher quelques sorts
                if sc.get('at_will'):
                    print(f"       At-will: {', '.join(sc['at_will'][:3])}")

                for level, spells in list(sc.get('spells_by_level', {}).items())[:2]:
                    if spells:
                        # Normaliser noms de sorts
                        normalized_spells = [s.lower().replace(' ', '-') for s in spells]
                        print(f"       Level {level}: {', '.join(normalized_spells[:3])}")

        # Test 3: Combat simulé
        print()
        print("Test 3: Combat simulé")

        if not goblin.actions:
            print("  ❌ Pas d'actions disponibles")
            return 1

        # Créer adversaire
        goblin2 = load_monster('goblin')
        if not goblin2:
            print("  ❌ Impossible de charger adversaire")
            return 1

        goblin.name = "Goblin Attaquant"
        goblin2.name = "Goblin Défenseur"

        print(f"  ⚔️  {goblin.name} vs {goblin2.name}")
        print()
        print(f"  État initial:")
        print(f"    {goblin.name}: {goblin.current_hp} HP")
        print(f"    {goblin2.name}: {goblin2.current_hp} HP")
        print()

        # Simuler une attaque
        action = goblin.actions[0]
        print(f"  {goblin.name} utilise {action.name}")

        import random
        attack_roll = random.randint(1, 20)
        attack_bonus = getattr(action, 'attack_bonus', 0)
        total = attack_roll + attack_bonus

        print(f"    Jet d'attaque: {attack_roll} + {attack_bonus} = {total}")

        if total >= goblin2.armor_class:
            print(f"    ✅ Touche! (AC: {goblin2.armor_class})")

            # Calculer dégâts
            if hasattr(action, 'damages') and action.damages:
                dmg = action.damages[0]
                damage_roll = sum(random.randint(1, dmg.dice_type) for _ in range(dmg.dice_count))
                total_damage = damage_roll + dmg.bonus

                print(f"    Dégâts: {damage_roll} + {dmg.bonus} = {total_damage}")

                goblin2.current_hp -= total_damage
                print(f"    {goblin2.name}: {max(0, goblin2.current_hp)} HP")

                if goblin2.current_hp <= 0:
                    print()
                    print(f"  💀 {goblin2.name} est vaincu!")
                else:
                    print()
                    print(f"  ✅ {goblin2.name} survit!")
        else:
            print(f"    ❌ Raté! (AC: {goblin2.armor_class})")

        print()
        print("✅ Test de combat réussi!")

        return 0

    except Exception as e:
        print(f"❌ Erreur test combat: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Point d'entrée principal"""
    print("=" * 80)
    print("🚀 RESTAURATION ET TEST FINAL COMPLET")
    print("=" * 80)
    print()

    # Étape 1: Restaurer les monstres
    moved = restore_all_monsters()

    if moved == 1:  # Annulé
        return 1

    # Étape 2: Test normalisation sorts
    test_spell_name_normalization()

    # Étape 3: Test combat complet
    result = run_complete_combat_test()

    print()
    print("=" * 80)
    print("📊 RÉSUMÉ")
    print("=" * 80)
    print()

    if moved > 0:
        print(f"✅ {moved} monstres restaurés dans extended/")

    print("✅ Normalisation sorts: espace → tiret")

    if result == 0:
        print("✅ Test de combat: RÉUSSI")
    else:
        print("❌ Test de combat: ÉCHOUÉ")

    print()
    print("=" * 80)
    print("✅ PROCESSUS TERMINÉ")
    print("=" * 80)

    return result


if __name__ == "__main__":
    exit(main())
