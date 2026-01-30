#!/usr/bin/env python3
"""
Script pour valider et organiser les fichiers de monstres dans extended/

Vérifie:
1. Structure des fichiers JSON
2. Présence d'actions
3. Compatibilité avec Monster class
4. Déplace les fichiers invalides vers invalid/
"""
import json
import shutil
from pathlib import Path
from typing import Dict, Any, List, Tuple


def analyze_monster_file(filepath: Path) -> Dict[str, Any]:
    """Analyse un fichier de monstre et retourne ses caractéristiques"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            monster = json.load(f)

        # Vérifier présence d'actions
        has_actions = bool(monster.get('action') or monster.get('actions'))

        # Compter les actions
        action_count = 0
        if 'action' in monster and isinstance(monster['action'], list):
            action_count = len(monster['action'])
        elif 'actions' in monster and isinstance(monster['actions'], list):
            action_count = len(monster['actions'])

        # Autres champs importants
        has_speed = 'speed' in monster
        has_hp = 'hp' in monster or 'hit_points' in monster
        has_ac = 'ac' in monster or 'armor_class' in monster
        has_abilities = all(k in monster for k in ['str', 'dex', 'con', 'int', 'wis', 'cha'])

        return {
            'valid': True,
            'has_actions': has_actions,
            'action_count': action_count,
            'has_speed': has_speed,
            'has_hp': has_hp,
            'has_ac': has_ac,
            'has_abilities': has_abilities,
            'name': monster.get('name', filepath.stem),
            'source': monster.get('source', 'Unknown'),
            'cr': monster.get('cr', 'Unknown'),
            'error': None
        }
    except json.JSONDecodeError as e:
        return {
            'valid': False,
            'error': f'JSON invalide: {e}',
            'has_actions': False
        }
    except Exception as e:
        return {
            'valid': False,
            'error': f'Erreur: {e}',
            'has_actions': False
        }


def main():
    """Point d'entrée principal"""
    print("=" * 80)
    print("🔍 VALIDATION DES FICHIERS DE MONSTRES EXTENDED")
    print("=" * 80)
    print()

    # Chemins
    extended_dir = Path(__file__).parent
    invalid_dir = extended_dir / 'invalid'

    # Trouver tous les fichiers JSON (sauf archives)
    exclude_files = {
        'bestiary-sublist-data.json',
        'bestiary-sublist-data-all-monsters.json',
        'bestiary-sublist-data_ori.json'
    }

    json_files = [
        f for f in extended_dir.glob('*.json')
        if f.name not in exclude_files
    ]

    print(f"📊 {len(json_files)} fichiers à analyser")
    print()

    # Statistiques
    stats = {
        'total': len(json_files),
        'valid': 0,
        'invalid': 0,
        'with_actions': 0,
        'without_actions': 0,
        'to_move': []
    }

    # Analyser chaque fichier
    print("🔍 Analyse en cours...")
    for i, filepath in enumerate(json_files, 1):
        analysis = analyze_monster_file(filepath)

        if analysis['valid']:
            stats['valid'] += 1

            if analysis['has_actions']:
                stats['with_actions'] += 1
            else:
                stats['without_actions'] += 1
                stats['to_move'].append({
                    'path': filepath,
                    'name': analysis['name'],
                    'reason': 'No actions'
                })
        else:
            stats['invalid'] += 1
            stats['to_move'].append({
                'path': filepath,
                'name': filepath.stem,
                'reason': analysis['error']
            })

        # Afficher progression
        if i % 100 == 0 or i == len(json_files):
            print(f"  [{i}/{len(json_files)}] Analysés")

    # Rapport
    print()
    print("=" * 80)
    print("📊 RAPPORT D'ANALYSE")
    print("=" * 80)
    print(f"Total de fichiers: {stats['total']}")
    print(f"  ✅ Fichiers valides: {stats['valid']}")
    print(f"  ❌ Fichiers invalides: {stats['invalid']}")
    print()
    print(f"  ✅ Avec actions: {stats['with_actions']}")
    print(f"  ❌ Sans actions: {stats['without_actions']}")
    print()

    if stats['to_move']:
        print(f"⚠️  {len(stats['to_move'])} fichiers à déplacer vers invalid/")
        print()

        # Demander confirmation
        response = input("Déplacer les fichiers sans actions vers invalid/ ? (oui/non): ")

        if response.lower() in ['oui', 'o', 'yes', 'y']:
            # Créer le répertoire invalid
            invalid_dir.mkdir(exist_ok=True)

            print()
            print("📦 Déplacement des fichiers...")
            moved = 0

            for item in stats['to_move']:
                try:
                    dest = invalid_dir / item['path'].name
                    shutil.move(str(item['path']), str(dest))
                    print(f"  ✅ {item['name']} → invalid/")
                    moved += 1
                except Exception as e:
                    print(f"  ❌ Erreur déplacement {item['name']}: {e}")

            print()
            print(f"✅ {moved} fichiers déplacés vers invalid/")
        else:
            print("❌ Déplacement annulé")

    print()
    print("=" * 80)
    print("✅ VALIDATION TERMINÉE")
    print("=" * 80)

    # Résumé final
    remaining = stats['total'] - len(stats['to_move'])
    print(f"📁 Fichiers restants dans extended/: {remaining}")
    print(f"📁 Fichiers déplacés dans invalid/: {len(stats['to_move']) if response.lower() in ['oui', 'o', 'yes', 'y'] else 0}")
    print()


if __name__ == "__main__":
    main()
