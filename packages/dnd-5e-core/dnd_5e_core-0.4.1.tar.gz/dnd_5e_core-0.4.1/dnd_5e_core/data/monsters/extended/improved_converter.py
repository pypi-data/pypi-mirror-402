#!/usr/bin/env python3
"""
Convertisseur amélioré 5e.tools → Monster Class

Ce script parse correctement:
1. Actions (avec regex pour extraire attack_bonus, damage, etc.)
2. Spellcasting (extraction des sorts depuis la liste connue)
3. Tous les champs requis pour Monster class
"""
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


class FiveEToolsActionParser:
    """Parse les actions depuis le format 5e.tools"""

    # Patterns regex pour parser les actions
    ATTACK_PATTERN = re.compile(r'\{@atk (mw|rw|ms|rs)\}')  # melee weapon, ranged weapon, melee spell, ranged spell
    HIT_PATTERN = re.compile(r'\{@hit (\d+)\}')  # bonus d'attaque
    DAMAGE_PATTERN = re.compile(r'\{@damage ([\dd\+\-\s]+)\}')  # dégâts (ex: 2d6 + 4)
    DC_PATTERN = re.compile(r'\{@dc (\d+)\}')  # Difficulty Class

    # Types d'attaque
    ATTACK_TYPES = {
        'mw': 'melee_weapon',
        'rw': 'ranged_weapon',
        'ms': 'melee_spell',
        'rs': 'ranged_spell'
    }

    def parse_action(self, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse une action au format 5e.tools

        :param action_data: Données action (name, entries)
        :return: Action parsée avec attack_bonus, damage, etc.
        """
        name = action_data.get('name', 'Unknown')
        entries = action_data.get('entries', [])

        # Combiner toutes les entrées en texte
        full_text = ' '.join(str(entry) for entry in entries)

        # Extraire les informations
        attack_type = self._extract_attack_type(full_text)
        attack_bonus = self._extract_attack_bonus(full_text)
        damages = self._extract_damages(full_text)
        dc = self._extract_dc(full_text)

        return {
            'name': name,
            'description': full_text,
            'attack_type': attack_type,
            'attack_bonus': attack_bonus,
            'damages': damages,
            'dc': dc,
            'entries': entries  # Garder original
        }

    def _extract_attack_type(self, text: str) -> Optional[str]:
        """Extrait le type d'attaque"""
        match = self.ATTACK_PATTERN.search(text)
        if match:
            return self.ATTACK_TYPES.get(match.group(1))
        return None

    def _extract_attack_bonus(self, text: str) -> Optional[int]:
        """Extrait le bonus d'attaque"""
        match = self.HIT_PATTERN.search(text)
        if match:
            return int(match.group(1))
        return None

    def _extract_damages(self, text: str) -> List[Dict[str, Any]]:
        """Extrait les dégâts"""
        damages = []
        for match in self.DAMAGE_PATTERN.finditer(text):
            damage_formula = match.group(1).strip()

            # Parser le dé (ex: "2d6 + 4")
            dice_match = re.match(r'(\d+)d(\d+)\s*([+\-]\s*\d+)?', damage_formula)
            if dice_match:
                count = int(dice_match.group(1))
                sides = int(dice_match.group(2))
                bonus = 0
                if dice_match.group(3):
                    bonus = int(dice_match.group(3).replace(' ', ''))

                damages.append({
                    'formula': damage_formula,
                    'dice_count': count,
                    'dice_sides': sides,
                    'bonus': bonus
                })

        return damages

    def _extract_dc(self, text: str) -> Optional[int]:
        """Extrait la Difficulty Class"""
        match = self.DC_PATTERN.search(text)
        if match:
            return int(match.group(1))
        return None


class FiveEToolsSpellParser:
    """Parse le spellcasting depuis le format 5e.tools"""

    # Pattern pour extraire les noms de sorts
    SPELL_PATTERN = re.compile(r'\{@spell ([^}|]+)(?:\|[^}]*)?\}')

    def __init__(self, spells_data_path: Optional[Path] = None):
        """
        Initialise le parser de sorts

        :param spells_data_path: Chemin vers data/spells
        """
        self.known_spells = self._load_known_spells(spells_data_path)

    def _load_known_spells(self, spells_path: Optional[Path]) -> set:
        """Charge la liste des sorts connus depuis data/spells"""
        if spells_path is None:
            # Chemin par défaut
            current = Path(__file__).parent
            spells_path = current.parent.parent / 'spells'

        known_spells = set()

        if spells_path.exists():
            for spell_file in spells_path.glob('*.json'):
                try:
                    with open(spell_file, 'r', encoding='utf-8') as f:
                        spell_data = json.load(f)
                        spell_name = spell_data.get('name', spell_file.stem)
                        known_spells.add(spell_name.lower())
                except:
                    pass

        return known_spells

    def parse_spellcasting(self, spellcasting_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Parse les données de spellcasting

        :param spellcasting_data: Liste des entrées spellcasting
        :return: Données parsées
        """
        if not spellcasting_data:
            return {}

        result = {
            'ability': None,
            'dc': None,
            'attack_bonus': None,
            'spells_by_level': {},
            'daily': {},
            'at_will': []
        }

        for sc_entry in spellcasting_data:
            # Extraire ability
            if 'ability' in sc_entry:
                result['ability'] = sc_entry['ability']

            # Extraire DC depuis headerEntries
            if 'headerEntries' in sc_entry:
                for header in sc_entry['headerEntries']:
                    dc_match = re.search(r'save\s+\{@dc\s+(\d+)\}', str(header))
                    if dc_match:
                        result['dc'] = int(dc_match.group(1))

            # Extraire sorts par niveau
            if 'spells' in sc_entry:
                for level, spell_data in sc_entry['spells'].items():
                    spells_list = spell_data.get('spells', [])
                    result['spells_by_level'][level] = self._extract_spells(spells_list)

            # Extraire daily spells
            if 'daily' in sc_entry:
                for freq, spells in sc_entry['daily'].items():
                    result['daily'][freq] = self._extract_spells(spells)

            # Extraire at-will
            if 'will' in sc_entry:
                result['at_will'] = self._extract_spells(sc_entry['will'])

        return result

    def _extract_spells(self, spells_data: Any) -> List[str]:
        """Extrait les noms de sorts depuis différents formats"""
        spells = []

        if isinstance(spells_data, list):
            for item in spells_data:
                extracted = self.SPELL_PATTERN.findall(str(item))
                spells.extend(extracted)
        elif isinstance(spells_data, str):
            extracted = self.SPELL_PATTERN.findall(spells_data)
            spells.extend(extracted)

        # Nettoyer et normaliser
        cleaned_spells = []
        for spell in spells:
            # Normaliser: lowercase + espaces → tirets
            # "Detect Magic" → "detect-magic"
            # "cure wounds" → "cure-wounds"
            spell_normalized = spell.strip().lower().replace(' ', '-')
            cleaned_spells.append(spell_normalized)

        return cleaned_spells


class ImprovedMonsterConverter:
    """Convertisseur amélioré 5e.tools → Monster class"""

    def __init__(self):
        self.action_parser = FiveEToolsActionParser()
        self.spell_parser = FiveEToolsSpellParser()

    def convert_monster(self, monster_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convertit un monstre 5e.tools vers le format Monster class

        :param monster_data: Données au format 5e.tools
        :return: Données converties
        """
        # Structure de base (déjà correcte dans les fichiers)
        converted = {
            'name': monster_data.get('name'),
            'size': monster_data.get('size'),
            'type': monster_data.get('type'),
            'alignment': monster_data.get('alignment'),
            'armor_class': monster_data.get('armor_class'),
            'hit_points': monster_data.get('hit_points'),
            'speed': monster_data.get('speed'),
            'abilities': monster_data.get('abilities'),
            'challenge_rating': monster_data.get('challenge_rating'),
            'source': monster_data.get('source'),

            # Parser les actions
            'actions_parsed': self._parse_actions(monster_data.get('action', [])),

            # Parser spellcasting
            'spellcasting_parsed': self.spell_parser.parse_spellcasting(
                monster_data.get('spellcasting', [])
            ),

            # Garder les données originales
            'trait': monster_data.get('trait', []),
            'action': monster_data.get('action', []),
            'reaction': monster_data.get('reaction', []),
            'legendary': monster_data.get('legendary', []),
            'spellcasting': monster_data.get('spellcasting', []),

            # Autres champs
            'saving_throws': monster_data.get('saving_throws', {}),
            'skills': monster_data.get('skills', {}),
            'damage_vulnerabilities': monster_data.get('damage_vulnerabilities', []),
            'damage_resistances': monster_data.get('damage_resistances', []),
            'damage_immunities': monster_data.get('damage_immunities', []),
            'condition_immunities': monster_data.get('condition_immunities', []),
            'senses': monster_data.get('senses', []),
            'languages': monster_data.get('languages', []),

            '_5etools': monster_data.get('_5etools', {})
        }

        return converted

    def _parse_actions(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse toutes les actions"""
        parsed_actions = []

        for action in actions:
            parsed = self.action_parser.parse_action(action)
            parsed_actions.append(parsed)

        return parsed_actions


def main():
    """Test du convertisseur"""
    print("=" * 80)
    print("🧪 TEST DU CONVERTISSEUR AMÉLIORÉ")
    print("=" * 80)
    print()

    # Tester avec aartuk-elder.json
    test_file = Path(__file__).parent / 'invalid' / 'aartuk-elder.json'

    if not test_file.exists():
        print(f"❌ Fichier de test non trouvé: {test_file}")
        return 1

    print(f"📖 Lecture de {test_file.name}...")

    with open(test_file, 'r', encoding='utf-8') as f:
        monster_data = json.load(f)

    print(f"✅ Monstre: {monster_data.get('name')}")
    print()

    # Convertir
    converter = ImprovedMonsterConverter()
    converted = converter.convert_monster(monster_data)

    # Afficher résultats
    print("📊 RÉSULTATS DE PARSING:")
    print()

    print("Actions parsées:")
    for action in converted['actions_parsed']:
        print(f"  • {action['name']}")
        print(f"    Type: {action.get('attack_type', 'N/A')}")
        print(f"    Bonus: +{action.get('attack_bonus', 'N/A')}")
        if action.get('damages'):
            for dmg in action['damages']:
                print(f"    Damage: {dmg['formula']} ({dmg['dice_count']}d{dmg['dice_sides']}+{dmg['bonus']})")
        print()

    print("Spellcasting parsé:")
    sc = converted['spellcasting_parsed']
    if sc:
        print(f"  Ability: {sc.get('ability', 'N/A')}")
        print(f"  DC: {sc.get('dc', 'N/A')}")

        if sc.get('daily'):
            print(f"  Daily spells:")
            for freq, spells in sc['daily'].items():
                print(f"    {freq}: {', '.join(spells)}")

        if sc.get('spells_by_level'):
            print(f"  Spells by level:")
            for level, spells in sc['spells_by_level'].items():
                print(f"    Level {level}: {', '.join(spells)}")
    else:
        print("  Aucun spellcasting")

    print()
    print("=" * 80)
    print("✅ TEST TERMINÉ")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    exit(main())
