#!/usr/bin/env python3
"""
Script de validation des monstres extraits

Vérifie que les fichiers JSON sont valides et compatibles avec Monster class
"""
import json
import sys
from pathlib import Path
from typing import Dict, Any, List


def validate_monster_file(filepath: Path) -> Dict[str, Any]:
    """Valide un fichier de monstre"""
    errors = []
    warnings = []

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            monster = json.load(f)
    except json.JSONDecodeError as e:
        return {
            "valid": False,
            "errors": [f"JSON invalide: {e}"],
            "warnings": []
        }
    except Exception as e:
        return {
            "valid": False,
            "errors": [f"Erreur lecture: {e}"],
            "warnings": []
        }

    # Vérifier champs requis
    required_fields = ['name', 'size', 'type', 'armor_class', 'hit_points', 'abilities']
    for field in required_fields:
        if field not in monster:
            errors.append(f"Champ requis manquant: {field}")

    # Vérifier structure abilities
    if 'abilities' in monster:
        required_abilities = ['str', 'dex', 'con', 'int', 'wis', 'cha']
        abilities = monster['abilities']
        if not isinstance(abilities, dict):
            errors.append("abilities doit être un dictionnaire")
        else:
            for ability in required_abilities:
                if ability not in abilities:
                    errors.append(f"Caractéristique manquante: {ability}")
                elif not isinstance(abilities[ability], int):
                    errors.append(f"{ability} doit être un entier")

    # Vérifier hit_points
    if 'hit_points' in monster:
        hp = monster['hit_points']
        if isinstance(hp, dict):
            if 'average' not in hp:
                warnings.append("hit_points.average manquant")
            if 'formula' not in hp:
                warnings.append("hit_points.formula manquant")
        elif not isinstance(hp, int):
            warnings.append("hit_points devrait être dict ou int")

    # Vérifier armor_class
    if 'armor_class' in monster and not isinstance(monster['armor_class'], int):
        warnings.append("armor_class devrait être un entier")

    # Vérifier speed
    if 'speed' in monster:
        if not isinstance(monster['speed'], dict):
            warnings.append("speed devrait être un dictionnaire")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


def main():
    """Point d'entrée principal"""
    print("=" * 80)
    print("✅ VALIDATION DES MONSTRES EXTRAITS")
    print("=" * 80)
    print()

    # Trouver tous les fichiers JSON
    extended_dir = Path(__file__).parent
    json_files = list(extended_dir.glob("*.json"))

    # Exclure les fichiers d'archive
    json_files = [f for f in json_files if f.name not in [
        'bestiary-sublist-data.json',
        'bestiary-sublist-data-all-monsters.json'
    ]]

    if not json_files:
        print("❌ Aucun fichier JSON trouvé")
        return 1

    print(f"📊 {len(json_files)} fichiers à valider")
    print()

    # Statistiques
    valid_count = 0
    invalid_count = 0
    warning_count = 0
    all_errors = []
    all_warnings = []

    # Valider chaque fichier
    for i, filepath in enumerate(json_files, 1):
        result = validate_monster_file(filepath)

        if result['valid']:
            valid_count += 1
        else:
            invalid_count += 1
            all_errors.extend([(filepath.name, err) for err in result['errors']])

        if result['warnings']:
            warning_count += 1
            all_warnings.extend([(filepath.name, warn) for warn in result['warnings']])

        # Afficher progression
        if i % 100 == 0 or i == len(json_files):
            print(f"  [{i}/{len(json_files)}] Validés: {valid_count}, Erreurs: {invalid_count}, Avertissements: {warning_count}")

    # Rapport final
    print()
    print("=" * 80)
    print("📊 RAPPORT DE VALIDATION")
    print("=" * 80)
    print(f"✅ Fichiers valides: {valid_count}/{len(json_files)}")
    print(f"❌ Fichiers invalides: {invalid_count}/{len(json_files)}")
    print(f"⚠️  Fichiers avec avertissements: {warning_count}/{len(json_files)}")

    if all_errors:
        print()
        print(f"❌ Erreurs ({len(all_errors)}):")
        for filename, error in all_errors[:20]:
            print(f"  • {filename}: {error}")
        if len(all_errors) > 20:
            print(f"  ... et {len(all_errors) - 20} autres erreurs")

    if all_warnings:
        print()
        print(f"⚠️  Avertissements ({len(all_warnings)}):")
        for filename, warning in all_warnings[:20]:
            print(f"  • {filename}: {warning}")
        if len(all_warnings) > 20:
            print(f"  ... et {len(all_warnings) - 20} autres avertissements")

    print()
    print("=" * 80)

    if invalid_count == 0:
        print("✅ VALIDATION RÉUSSIE!")
        return 0
    else:
        print(f"⚠️  VALIDATION TERMINÉE AVEC {invalid_count} ERREURS")
        return 1


if __name__ == "__main__":
    exit(main())
