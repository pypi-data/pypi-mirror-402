# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.7] - 2026-01-18

### Added
- **PyPI Optimization** - Amélioration complète des métadonnées PyPI
  - Description mise à jour avec les nouvelles fonctionnalités majeures
  - 32 mots-clés ajoutés pour une meilleure découvrabilité
  - Métadonnées complètes pour le positionnement "Ultimate D&D 5e Rules Engine"

### Changed
- **CHANGELOG Synthesis** - Synthèse des anciennes versions pour lisibilité
  - Réduction de ~570 à ~200 lignes (65% de réduction)
  - Conservation des changements majeurs
  - Suppression des détails techniques répétitifs

### Fixed
- **Version Consistency** - Synchronisation parfaite des versions
  - pyproject.toml, setup.py, et __init__.py alignés
  - Prévention des conflits de publication PyPI

## [0.2.6] - 2026-01-18

### Added
- **ClassAbilities** - Système complet des capacités de classe
  - 24 capacités implémentées pour toutes les classes
  - Barbarian: Rage, Reckless Attack
  - Fighter: Action Surge, Second Wind, Extra Attack
  - Rogue: Sneak Attack, Cunning Action, Uncanny Dodge
  - Monk: Ki Points, Flurry of Blows, Martial Arts
  - Cleric: Channel Divinity
  - Paladin: Lay on Hands, Divine Smite
  - Bard: Bardic Inspiration
  - Sorcerer: Sorcery Points, Metamagic
  - Ranger: Hunter's Mark
  - Warlock: Eldritch Invocations

- **RacialTraits** - Système complet des traits raciaux
  - 20 traits implémentés pour toutes les races
  - Elf: Darkvision, Fey Ancestry, Trance, Keen Senses, Mask of the Wild
  - Dwarf: Dwarven Resilience, Stonecunning, Dwarven Toughness
  - Halfling: Lucky, Brave, Halfling Nimbleness, Naturally Stealthy
  - Human: Versatility
  - Dragonborn: Breath Weapon, Damage Resistance
  - Gnome: Gnome Cunning
  - Half-Orc: Relentless Endurance, Savage Attacks
  - Tiefling: Hellish Resistance, Infernal Legacy

- **Subclass System** - Sous-classes et multiclassing
  - Support de 40+ sous-classes (Champion, Evocation, Life Domain, etc.)
  - Support de 20+ sous-races (High Elf, Hill Dwarf, etc.)
  - Système de multiclassing avec calcul automatique des spell slots
  - `MulticlassCharacter` pour gérer plusieurs classes

### Fixed
- Parsing robuste des `saving_throws` (gestion des AbilityType)
- Parsing sécurisé des données JSON de subclasses et subraces
- Corrections dans le système de progression des classes

### Changed
- Archivage de 36 fichiers obsolètes vers `archive/2026-01-docs/` et `archive/2026-01-scripts/`
- Structure du projet épurée (6 documents MD essentiels à la racine)
- Script `build_package.sh` amélioré avec options complètes

## [0.2.4] - 2026-01-18

### Added
- **ConditionParser** - Système de parsing automatique des conditions depuis descriptions textuelles
- **Magic Items with Conditions** - Objets magiques appliquant des conditions
- **Monster Condition Application** - Application automatique des conditions par les monstres

### Changed
- **Monster.attack()** - Amélioration de l'application des conditions

## [0.2.3] - 2026-01-18

### Changed
- **ARCHITECTURE MAJEURE** - Réorganisation complète des données dans le package
- Tous les fichiers JSON (monsters, spells, equipment, etc.) sont maintenant dans `dnd_5e_core/data/`
- Les données sont **toujours incluses** dans le package installé

## [0.2.2] - 2026-01-18

### Fixed
- **Condition Class Implementation** - Migration complète de `Condition` depuis `dao_classes.py`
- 14 fonctions helper pour toutes les conditions D&D 5e standard

## [0.2.1] - 2026-01-18

### Added
- **Conditions System** - Système complet de conditions D&D 5e
- **Magic Items System** - Objets magiques avec actions de combat
- **Defensive Spells System** - Sorts défensifs avec bonus AC et sauvegardes

## [0.2.0] - 2026-01-18

### Added
- **Magic Items System** - Objets magiques avec bonus passifs et actions actives
- **Defensive Spells System** - Sorts défensifs (Shield, Mage Armor, etc.)
- 8 objets magiques prédéfinis (Ring of Protection, Wand of Magic Missiles, etc.)

## [0.1.9] - 2026-01-17

### Changed
- **BREAKING CHANGE**: Toutes les fonctions `load_*()` retournent maintenant des objets au lieu de dictionnaires
- Migration complète vers une API orientée objet

## [0.1.4] - 2026-01-05

### Added
- **Implémentation complète** de toutes les classes vides (28 classes migrées)
- **Système d'expérience** complet avec niveaux 1-20
- **Multiclassing** avec prérequis et calculs de spell slots
- **Challenge Rating** et difficulté de rencontres
- **26+ fonctions utilitaires** (dice rolling, modifiers, combat, etc.)
- **200+ constantes** du jeu D&D 5e

## [0.1.3] - 2026-01-05

### Fixed
- Inclusion correcte des données de monstres dans le package distribué

## [0.1.2] - 2026-01-05

### Added
- **Documentation complète** pour la publication PyPI et GitHub
- Métadonnées PyPI complètes avec 11 mots-clés

## [0.1.1] - 2026-01-03

### Added
- Métadonnées PyPI complètes pour meilleure découvrabilité
- Configuration GitHub "About" section

## [0.1.0] - 2025-12-24

### Added
- **Intégration majeure** du répertoire Collections D&D 5e API (26 index files)
- **Intégration majeure** des données JSON D&D 5e (8.7 MB, 2000+ fichiers)
- Structure de package initiale avec entités, races, classes, équipements
- Système de combat avec actions et capacités spéciales
- Chargeur de données depuis fichiers JSON locaux

### Changed
- Auto-détection des répertoires de données (plus de configuration manuelle)
- Priorité de chargement : package inclus → API DnD-5th-Edition-API → ./data

## [0.1.0] - 2025-01-XX

### Added
- Première release alpha
- Mécaniques de base D&D 5e implémentées
