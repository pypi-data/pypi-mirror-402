#!/usr/bin/env python3
"""
Script de ré-analyse et enrichissement des monstres extended

Utilise le convertisseur amélioré pour:
1. Parser toutes les actions avec regex
2. Extraire les sorts depuis spellcasting
3. Créer des fichiers enrichis avec données parsées
4. Valider que TOUS les monstres ont des actions
"""
import json
import shutil
from pathlib import Path
from typing import Dict, Any, List
import sys

# Importer le convertisseur
sys.path.insert(0, str(Path(__file__).parent))
from improved_converter import ImprovedMonsterConverter


def main():
    """Point d'entrée principal"""
    print("=" * 80)
    print("🔄 RÉ-ANALYSE ET ENRICHISSEMENT DES MONSTRES EXTENDED")
    print("=" * 80)
    print()
    
    # Chemins
    extended_dir = Path(__file__).parent
    invalid_dir = extended_dir / 'invalid'
    enriched_dir = extended_dir / 'enriched'
    
    # Créer répertoire enriched
    enriched_dir.mkdir(exist_ok=True)
    
    # Trouver tous les fichiers JSON
    exclude_files = {
        'bestiary-sublist-data.json',
        'bestiary-sublist-data-all-monsters.json',
        'bestiary-sublist-data_ori.json'
    }
    
    json_files = sorted([
        f for f in extended_dir.glob('*.json')
        if f.name not in exclude_files
    ])
    
    # Aussi chercher dans invalid/ si existe
    if invalid_dir.exists():
        invalid_files = list(invalid_dir.glob('*.json'))
        if invalid_files:
            print(f"⚠️  {len(invalid_files)} fichiers trouvés dans invalid/")
            response = input("Les inclure dans l'analyse? (oui/non): ")
            if response.lower() in ['oui', 'o', 'yes', 'y']:
                json_files.extend(invalid_files)
    
    print(f"📊 {len(json_files)} fichiers à analyser")
    print()
    
    # Créer le convertisseur
    converter = ImprovedMonsterConverter()
    
    # Statistiques
    stats = {
        'total': len(json_files),
        'processed': 0,
        'with_actions': 0,
        'without_actions': 0,
        'with_spells': 0,
        'errors': [],
        'to_keep': [],
        'to_remove': []
    }
    
    # Traiter chaque fichier
    print("🔍 Analyse et enrichissement...")
    print()
    
    for i, filepath in enumerate(json_files, 1):
        try:
            # Charger le fichier original
            with open(filepath, 'r', encoding='utf-8') as f:
                monster_data = json.load(f)
            
            name = monster_data.get('name', filepath.stem)
            
            # Vérifier présence d'actions
            has_actions = bool(monster_data.get('action'))
            action_count = len(monster_data.get('action', []))
            
            if has_actions and action_count > 0:
                stats['with_actions'] += 1
                stats['to_keep'].append(filepath)
                
                # Convertir et enrichir
                enriched = converter.convert_monster(monster_data)
                
                # Vérifier spellcasting
                if enriched.get('spellcasting_parsed') and enriched['spellcasting_parsed']:
                    stats['with_spells'] += 1
                
                # Sauvegarder version enrichie
                enriched_file = enriched_dir / filepath.name
                with open(enriched_file, 'w', encoding='utf-8') as f:
                    json.dump(enriched, f, indent=2, ensure_ascii=False)
                
                stats['processed'] += 1
            else:
                stats['without_actions'] += 1
                stats['to_remove'].append(filepath)
            
            # Progression
            if i % 100 == 0:
                print(f"  [{i}/{len(json_files)}] Traités: {stats['processed']}, "
                      f"Avec actions: {stats['with_actions']}, "
                      f"Sans actions: {stats['without_actions']}")
        
        except Exception as e:
            stats['errors'].append({
                'file': filepath.name,
                'error': str(e)
            })
    
    # Rapport final
    print()
    print("=" * 80)
    print("📊 RAPPORT FINAL")
    print("=" * 80)
    print()
    print(f"Total analysé: {stats['total']}")
    print(f"  ✅ Avec actions: {stats['with_actions']}")
    print(f"  ✅ Avec sorts: {stats['with_spells']}")
    print(f"  ❌ Sans actions: {stats['without_actions']}")
    print(f"  ❌ Erreurs: {len(stats['errors'])}")
    print()
    print(f"📁 Fichiers enrichis créés dans: {enriched_dir}/")
    print(f"   {stats['processed']} monstres enrichis")
    print()
    
    # Afficher quelques exemples de parsing
    if stats['processed'] > 0:
        print("📝 Exemples de parsing (premiers 3 monstres):")
        for filepath in stats['to_keep'][:3]:
            enriched_file = enriched_dir / filepath.name
            if enriched_file.exists():
                with open(enriched_file, 'r', encoding='utf-8') as f:
                    enriched = json.load(f)
                
                print(f"\n  {enriched['name']}:")
                
                # Actions
                if enriched.get('actions_parsed'):
                    print(f"    Actions: {len(enriched['actions_parsed'])}")
                    for action in enriched['actions_parsed'][:2]:
                        print(f"      • {action['name']} (bonus: +{action.get('attack_bonus', 'N/A')})")
                
                # Spells
                if enriched.get('spellcasting_parsed'):
                    sc = enriched['spellcasting_parsed']
                    total_spells = sum(
                        len(spells) 
                        for spells in sc.get('spells_by_level', {}).values()
                    )
                    if total_spells > 0:
                        print(f"    Sorts: {total_spells} sorts")
    
    # Déplacer fichiers sans actions vers invalid/
    if stats['to_remove']:
        print()
        print(f"⚠️  {len(stats['to_remove'])} fichiers sans actions")
        response = input("Déplacer vers invalid/ ? (oui/non): ")
        
        if response.lower() in ['oui', 'o', 'yes', 'y']:
            invalid_dir.mkdir(exist_ok=True)
            
            moved = 0
            for filepath in stats['to_remove']:
                try:
                    dest = invalid_dir / filepath.name
                    shutil.move(str(filepath), str(dest))
                    moved += 1
                except Exception as e:
                    print(f"  ❌ Erreur déplacement {filepath.name}: {e}")
            
            print(f"✅ {moved} fichiers déplacés vers invalid/")
    
    print()
    print("=" * 80)
    print("✅ ENRICHISSEMENT TERMINÉ")
    print("=" * 80)
    print()
    print(f"📁 Fichiers originaux: extended/")
    print(f"📁 Fichiers enrichis: enriched/ ({stats['processed']} fichiers)")
    print(f"📁 Fichiers invalides: invalid/ ({len(stats['to_remove'])} fichiers)")
    print()
    
    return 0


if __name__ == "__main__":
    exit(main())
