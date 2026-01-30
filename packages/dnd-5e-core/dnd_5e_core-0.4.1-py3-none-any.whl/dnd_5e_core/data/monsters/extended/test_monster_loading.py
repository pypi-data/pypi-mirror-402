#!/usr/bin/env python3
"""
Script de test complet pour les monstres extended

Vérifie:
1. Présence d'actions dans tous les fichiers
2. Fonction de chargement FiveEToolsMonsterLoader
3. Compatibilité avec classe Monster
4. Archive les fichiers invalides
"""
import json
import shutil
import sys
from pathlib import Path
from typing import Dict, Any, List

# Ajouter le chemin du package
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from dnd_5e_core.entities import FiveEToolsMonsterLoader


def check_monster_structure(monster_data: Dict[str, Any]) -> Dict[str, Any]:
    """Vérifie la structure d'un monstre"""
    issues = []

    # Champs requis pour Monster class
    required_fields = {
        'name': 'Nom du monstre',
        'size': 'Taille',
        'type': 'Type de créature',
    }

    for field, description in required_fields.items():
        if field not in monster_data:
            issues.append(f"Champ requis manquant: {field} ({description})")

    # Vérifier actions (format 5e.tools)
    has_actions = 'action' in monster_data
    if not has_actions:
        issues.append("Aucune action définie (clé 'action' manquante)")
    elif isinstance(monster_data['action'], list) and len(monster_data['action']) == 0:
        issues.append("Liste d'actions vide")

    # Vérifier abilities (format 5e.tools)
    ability_scores = ['str', 'dex', 'con', 'int', 'wis', 'cha']
    missing_abilities = [ab for ab in ability_scores if ab not in monster_data]
    if missing_abilities:
        issues.append(f"Caractéristiques manquantes: {', '.join(missing_abilities)}")

    # Champs recommandés
    recommended = ['ac', 'hp', 'speed', 'cr']
    missing_recommended = [field for field in recommended if field not in monster_data]

    return {
        'valid': len(issues) == 0,
        'has_actions': has_actions,
        'issues': issues,
        'missing_recommended': missing_recommended
    }


def main():
    """Point d'entrée principal"""
    print("=" * 80)
    print("🔍 VALIDATION COMPLÈTE DES MONSTRES EXTENDED")
    print("=" * 80)
    print()

    # Chemins
    extended_dir = Path(__file__).parent
    invalid_dir = extended_dir / 'invalid'

    # Fichiers à exclure
    exclude_files = {
        'bestiary-sublist-data.json',
        'bestiary-sublist-data-all-monsters.json',
        'bestiary-sublist-data_ori.json'
    }

    # Trouver tous les fichiers JSON
    json_files = sorted([
        f for f in extended_dir.glob('*.json')
        if f.name not in exclude_files
    ])

    print(f"📊 {len(json_files)} fichiers à valider")
    print()

    # Statistiques
    stats = {
        'total': len(json_files),
        'valid': 0,
        'invalid': 0,
        'with_actions': 0,
        'without_actions': 0,
        'loader_success': 0,
        'loader_fail': 0,
        'to_archive': []
    }

    # Créer le loader
    print("🔧 Initialisation du loader...")
    try:
        loader = FiveEToolsMonsterLoader()
        print("✅ Loader initialisé\n")
    except Exception as e:
        print(f"❌ Erreur initialisation loader: {e}\n")
        return 1

    # Analyser chaque fichier
    print("🔍 Validation en cours...\n")

    for i, filepath in enumerate(json_files, 1):
        try:
            # Charger le fichier directement
            with open(filepath, 'r', encoding='utf-8') as f:
                monster_data = json.load(f)

            # Vérifier la structure
            check_result = check_monster_structure(monster_data)

            name = monster_data.get('name', filepath.stem)

            if check_result['valid']:
                stats['valid'] += 1

                if check_result['has_actions']:
                    stats['with_actions'] += 1
                else:
                    stats['without_actions'] += 1
                    stats['to_archive'].append({
                        'path': filepath,
                        'name': name,
                        'reason': 'Sans actions'
                    })

                # Tester le loader
                try:
                    loaded = loader.get_monster_by_name(name)
                    if loaded:
                        stats['loader_success'] += 1
                    else:
                        stats['loader_fail'] += 1
                except:
                    stats['loader_fail'] += 1
            else:
                stats['invalid'] += 1
                stats['to_archive'].append({
                    'path': filepath,
                    'name': name,
                    'reason': '; '.join(check_result['issues'][:2])
                })

            # Afficher progression
            if i % 100 == 0:
                print(f"  [{i}/{len(json_files)}] Validés: {stats['valid']}, "
                      f"Invalides: {stats['invalid']}, "
                      f"Sans actions: {stats['without_actions']}")

        except json.JSONDecodeError as e:
            stats['invalid'] += 1
            stats['to_archive'].append({
                'path': filepath,
                'name': filepath.stem,
                'reason': f'JSON invalide: {e}'
            })
        except Exception as e:
            stats['invalid'] += 1
            stats['to_archive'].append({
                'path': filepath,
                'name': filepath.stem,
                'reason': f'Erreur: {e}'
            })

    # Rapport final
    print()
    print("=" * 80)
    print("📊 RAPPORT DE VALIDATION")
    print("=" * 80)
    print(f"\n📁 Fichiers analysés: {stats['total']}")
    print(f"\n✅ Fichiers valides: {stats['valid']}")
    print(f"   • Avec actions: {stats['with_actions']}")
    print(f"   • Sans actions: {stats['without_actions']}")
    print(f"\n❌ Fichiers invalides: {stats['invalid']}")
    print(f"\n🔧 Test du loader:")
    print(f"   • Succès: {stats['loader_success']}")
    print(f"   • Échecs: {stats['loader_fail']}")

    # Fichiers à archiver
    if stats['to_archive']:
        print(f"\n⚠️  {len(stats['to_archive'])} fichiers à archiver:")

        # Grouper par raison
        by_reason = {}
        for item in stats['to_archive']:
            reason = item['reason']
            if reason not in by_reason:
                by_reason[reason] = []
            by_reason[reason].append(item['name'])

        for reason, names in by_reason.items():
            print(f"\n  {reason} ({len(names)} fichiers):")
            for name in names[:5]:
                print(f"    • {name}")
            if len(names) > 5:
                print(f"    ... et {len(names) - 5} autres")

        # Demander confirmation
        print()
        response = input("Déplacer les fichiers invalides vers invalid/ ? (oui/non): ")

        if response.lower() in ['oui', 'o', 'yes', 'y']:
            # Créer le répertoire invalid
            invalid_dir.mkdir(exist_ok=True)

            print()
            print("📦 Archivage des fichiers...")
            archived = 0

            for item in stats['to_archive']:
                try:
                    dest = invalid_dir / item['path'].name
                    shutil.move(str(item['path']), str(dest))
                    archived += 1
                    if archived % 100 == 0:
                        print(f"  [{archived}/{len(stats['to_archive'])}] Archivés...")
                except Exception as e:
                    print(f"  ❌ Erreur archivage {item['name']}: {e}")

            print(f"\n✅ {archived} fichiers archivés dans invalid/")

            # Rapport final
            remaining = stats['total'] - archived
            print()
            print("=" * 80)
            print("📊 RÉSULTAT FINAL")
            print("=" * 80)
            print(f"📁 Fichiers restants dans extended/: {remaining}")
            print(f"📁 Fichiers archivés dans invalid/: {archived}")
        else:
            print("\n❌ Archivage annulé")
    else:
        print("\n✅ Tous les fichiers sont valides!")

    print()
    print("=" * 80)
    print("✅ VALIDATION TERMINÉE")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    exit(main())
