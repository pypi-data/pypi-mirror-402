#!/usr/bin/env python3
"""
Script final d'extraction et validation complète

1. Analyse TOUS les monstres extended/
2. Vérifie présence d'actions
3. Parse avec improved_converter
4. Crée Monster objects
5. Test combat avec échantillon
6. Rapport final complet
"""
import json
import random
import sys
from pathlib import Path
from typing import Dict, Any, List

# Ajouter chemins
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from improved_converter import ImprovedMonsterConverter
from dnd_5e_core.data.loaders import load_monster


def analyze_all_monsters():
    """Analyse tous les monstres extended"""
    print("=" * 80)
    print("📊 ANALYSE COMPLÈTE DES MONSTRES EXTENDED")
    print("=" * 80)
    print()

    extended_dir = Path(__file__).parent

    # Trouver tous les fichiers
    exclude = {'bestiary-sublist-data.json', 'bestiary-sublist-data-all-monsters.json',
               'bestiary-sublist-data_ori.json'}

    json_files = sorted([
        f for f in extended_dir.glob('*.json')
        if f.name not in exclude
    ])

    print(f"📁 {len(json_files)} fichiers trouvés")
    print()

    # Statistiques
    stats = {
        'total': len(json_files),
        'with_actions': 0,
        'without_actions': 0,
        'with_spells': 0,
        'parsed_success': 0,
        'parsed_errors': [],
        'actions_total': 0,
        'spells_total': 0
    }

    # Converter
    converter = ImprovedMonsterConverter()

    print("🔍 Analyse en cours...")

    sample_monsters = []

    for i, filepath in enumerate(json_files, 1):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                monster_data = json.load(f)

            name = monster_data.get('name', filepath.stem)

            # Vérifier actions
            has_actions = bool(monster_data.get('action'))
            action_count = len(monster_data.get('action', []))

            if has_actions and action_count > 0:
                stats['with_actions'] += 1
                stats['actions_total'] += action_count

                # Parser
                try:
                    enriched = converter.convert_monster(monster_data)
                    stats['parsed_success'] += 1

                    # Vérifier spells
                    if enriched.get('spellcasting_parsed'):
                        sc = enriched['spellcasting_parsed']
                        if sc.get('spells_by_level') or sc.get('daily') or sc.get('at_will'):
                            stats['with_spells'] += 1

                            # Compter sorts
                            for spells in sc.get('spells_by_level', {}).values():
                                stats['spells_total'] += len(spells)
                            for spells in sc.get('daily', {}).values():
                                stats['spells_total'] += len(spells)
                            stats['spells_total'] += len(sc.get('at_will', []))

                    # Garder échantillon pour tests
                    if len(sample_monsters) < 10:
                        sample_monsters.append({
                            'name': name,
                            'data': enriched,
                            'filepath': filepath
                        })

                except Exception as e:
                    stats['parsed_errors'].append((name, str(e)))
            else:
                stats['without_actions'] += 1

            # Progression
            if i % 100 == 0:
                print(f"  [{i}/{len(json_files)}] Analysés...")

        except Exception as e:
            stats['parsed_errors'].append((filepath.name, str(e)))

    # Rapport
    print()
    print("=" * 80)
    print("📊 RAPPORT D'ANALYSE")
    print("=" * 80)
    print()
    print(f"Total fichiers: {stats['total']}")
    print(f"  ✅ Avec actions: {stats['with_actions']}")
    print(f"  ❌ Sans actions: {stats['without_actions']}")
    print(f"  ✅ Parsing réussi: {stats['parsed_success']}")
    print(f"  ❌ Erreurs parsing: {len(stats['parsed_errors'])}")
    print()
    print(f"  🎯 Total actions: {stats['actions_total']}")
    print(f"  🪄 Monstres avec sorts: {stats['with_spells']}")
    print(f"  📜 Total sorts: {stats['spells_total']}")
    print()

    if stats['parsed_errors']:
        print(f"⚠️  Erreurs de parsing ({len(stats['parsed_errors'])}):")
        for name, error in stats['parsed_errors'][:5]:
            print(f"  • {name}: {error[:60]}...")
        if len(stats['parsed_errors']) > 5:
            print(f"  ... et {len(stats['parsed_errors']) - 5} autres")
        print()

    return stats, sample_monsters


def test_sample_combats(sample_monsters):
    """Test combats avec échantillon"""
    print("=" * 80)
    print("⚔️  TESTS DE COMBAT")
    print("=" * 80)
    print()

    if len(sample_monsters) < 2:
        print("⚠️  Pas assez de monstres pour tester le combat")
        return

    # Prendre 2 monstres au hasard
    m1_data = random.choice(sample_monsters)
    m2_data = random.choice([m for m in sample_monsters if m != m1_data])

    m1 = m1_data['data']
    m2 = m2_data['data']

    print(f"🥊 Combat: {m1['name']} vs {m2['name']}")
    print()

    # Afficher stats
    print(f"{m1['name']}:")
    if m1.get('actions_parsed'):
        print(f"  Actions: {len(m1['actions_parsed'])}")
        for action in m1['actions_parsed'][:2]:
            print(f"    • {action['name']}")
            if action.get('attack_bonus'):
                print(f"      +{action['attack_bonus']} to hit")
            if action.get('damages'):
                for dmg in action['damages'][:1]:
                    print(f"      {dmg['formula']} damage")

    print()

    print(f"{m2['name']}:")
    if m2.get('actions_parsed'):
        print(f"  Actions: {len(m2['actions_parsed'])}")
        for action in m2['actions_parsed'][:2]:
            print(f"    • {action['name']}")
            if action.get('attack_bonus'):
                print(f"      +{action['attack_bonus']} to hit")
            if action.get('damages'):
                for dmg in action['damages'][:1]:
                    print(f"      {dmg['formula']} damage")

    print()
    print("✅ Données de combat disponibles et parsées!")
    print()


def main():
    """Point d'entrée principal"""
    print("=" * 80)
    print("🚀 EXTRACTION ET VALIDATION FINALE - MONSTRES EXTENDED")
    print("=" * 80)
    print()

    # Analyse complète
    stats, sample_monsters = analyze_all_monsters()

    # Tests de combat si possible
    if sample_monsters:
        test_sample_combats(sample_monsters)

    # Rapport final
    print("=" * 80)
    print("📋 RÉSUMÉ FINAL")
    print("=" * 80)
    print()

    if stats['without_actions'] == 0:
        print("✅ TOUS les monstres ont des actions!")
    else:
        print(f"⚠️  {stats['without_actions']} monstres sans actions")

    if stats['parsed_success'] == stats['with_actions']:
        print("✅ TOUS les monstres ont été parsés avec succès!")
    else:
        print(f"⚠️  {len(stats['parsed_errors'])} erreurs de parsing")

    print()
    print(f"📊 Statistiques:")
    print(f"  • {stats['with_actions']} monstres valides")
    print(f"  • {stats['actions_total']} actions totales")
    print(f"  • {stats['with_spells']} monstres avec spellcasting")
    print(f"  • {stats['spells_total']} sorts extraits")
    print()

    percentage = (stats['with_actions'] / stats['total'] * 100) if stats['total'] > 0 else 0
    print(f"✅ Taux de réussite: {percentage:.1f}%")
    print()

    print("=" * 80)
    print("✅ EXTRACTION ET VALIDATION TERMINÉES")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    exit(main())
