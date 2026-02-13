# CI/CD Pipeline Documentation

Ce projet utilise **GitHub Actions** pour assurer la qualité du code et la préparation au déploiement.

## 🔄 Workflow : `.github/workflows/ci.yml`

À chaque push sur `main` ou création d'une Pull Request, les jobs suivants sont exécutés :

### 1. 🧪 Job de Test (`test`)
- **Environnement** : Ubuntu Latest, Python 3.11
- **Étapes** :
    1.  Installation des dépendances depuis `ml/requirements.txt` et `api/requirements.txt`.
    2.  Exécution de **Pytest** sur `api/tests/`.
- **Objectif** : Détecter les régressions logiques avant la fusion (merge).

### 2. 🐳 Job de Build (`build-docker`)
- **Dépendance** : Exécuté uniquement si `test` réussit.
- **Étapes** :
    1.  Construction de l'image Docker pour l'API (`Dockerfile`).
- **Objectif** : Garantir que l'application peut être conteneurisée avec succès (fichiers manquants, erreurs de syntaxe Dockerfile).

## ✅ Comment Vérifier le Statut du Build
1.  Allez dans l'onglet **Actions** du dépôt GitHub.
2.  Cliquez sur la dernière exécution du workflow.
3.  Les coches vertes indiquent le succès. Les croix rouges indiquent un échec (vérifiez les logs).

## 🛠 Ajouter de Nouveaux Tests
Créez de nouveaux fichiers de test dans `api/tests/` nommés `test_*.py`.
Exemple :
```python
def test_exemple():
    assert 1 + 1 == 2
```
Ils seront automatiquement pris en compte par le pipeline CI.
