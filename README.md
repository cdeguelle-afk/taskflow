# Taskflow

Taskflow est une mini-application web inspirée de Todoist pour organiser vos tâches par projet, gérer leurs priorités et suivre votre progression quotidienne.

## Fonctionnalités principales

- Gestion de projets colorés avec une boîte de réception créée automatiquement
- Création, édition, suppression et complétion de tâches
- Filtrage par état (actives ou terminées), date d'échéance et recherche textuelle
- Résumé en temps réel du nombre total de tâches, terminées et actives
- Interface responsive avec formulaire rapide pour ajouter de nouvelles tâches

## Démarrage

### Installation des dépendances

```bash
pip install -r requirements.txt
```

### Lancer le serveur de développement

```bash
uvicorn app.main:app --reload
```

Le serveur expose l'API RESTful sous le préfixe `/api` et sert l'interface web sur [http://localhost:8000](http://localhost:8000).

## Tests

```bash
pytest
```

Les tests utilisent une base de données SQLite en mémoire et vérifient les principaux parcours de création et mise à jour des projets et des tâches.
