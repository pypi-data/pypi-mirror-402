# Monstres Invalides
Ce répertoire contient les fichiers de monstres qui ont été archivés car ils ne respectent pas les critères de validation.
## 📋 Raisons d'Archivage
Les fichiers peuvent être ici pour plusieurs raisons:
### 1. ❌ Sans Actions
Le monstre n'a pas de clé `action` ou la liste est vide.
**Exemple:**
```json
{
  "name": "Animated Object",
  "type": "construct",
  // PAS de clé "action"
}
```
**Solution:** Ajouter au moins une action au monstre.
### 2. ❌ JSON Invalide
Erreur de syntaxe JSON (virgule manquante, guillemets, etc.)
**Solution:** Corriger la syntaxe JSON.
### 3. ❌ Champs Requis Manquants
Le monstre n'a pas les champs minimum requis (name, size, type).
**Solution:** Ajouter les champs manquants.
### 4. ❌ Structure Incorrecte
Le fichier ne peut pas être chargé par FiveEToolsMonsterLoader.
**Solution:** Vérifier le format 5e.tools.
## 🔄 Restauration
Pour restaurer un monstre après correction:
```bash
# 1. Corriger le fichier dans invalid/
vim invalid/monstre.json
# 2. Valider manuellement
python3 -c "import json; json.load(open('invalid/monstre.json'))"
# 3. Déplacer vers extended/
mv invalid/monstre.json ../
# 4. Re-valider
cd ..
pythpythpythpythpythpythpythpythpythpythpythpythpythpythpPour voir combien de fichiers sont archivés:
```bash
ls -1 | wc -l
```
Pour voir les raisons (si fichier de log existe):
```bash
cat vacat vacat vacat v```
## ⚠️ Important
Les fichiers dans ce répertoire NE SONT PAS chargés par le FiveEToLes fichiers dans Si vous avez besoin d'un de ces monstres:
1. Corrigez le fichier
2. Restaurez-le dans `extended/`
3. Re-validez
## 📝 Format Attendu
Un monstre valide doit avoir au minimum:
```json
{
  "name": "Monster Name",
  "size": ["M"],
  "type": "beast",
  "str": 10,
  "dex": 10,
  "con": 10,
  "int": 10,
  "wis": 10,
  "cha": 10,
  "action": [
    {
      "name": "Attack",
      "entries": ["Description of the attack..."]
    }
  ]
}
```
---
**Note:** Ce répertoire est géré automatiquement par les scripts de validation.
