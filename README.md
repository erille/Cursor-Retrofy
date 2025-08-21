# Retrofy

Application Spotify-like minimaliste basée sur Flask, connectée à une base SQLite existante, avec recherche, fiches détaillées, récupération automatique de pochettes via MusicBrainz/Cover Art Archive (sans clé API) et téléversement manuel (protégé par authentification). Tout tourne dans Docker et s'expose sur le port 8888.

## Prérequis serveur
- Docker et docker-compose installés
- Base SQLite existante montée sur l'hôte: `/srv/sqlite/ma_base.sqlite`

## Lancer avec Docker
```bash
docker compose up --build -d
```
Application: `http://<votre-serveur>:8888`

Montages hôte:
- `/srv/sqlite` (RO) → DB SQLite existante
- `/srv/retrofy_images` (RW) → stockage persistant des pochettes

## Variables d'environnement
- `DB_PATH` (défaut `/srv/sqlite/ma_base.sqlite`)
- `IMAGES_DIR` (défaut `/data/images`)
- `SECRET_KEY` (à personnaliser en prod)

## Fonctionnalités
- Recherche: texte, artiste, année, genre
- Grille d'albums avec pochettes
- Détail: toutes les infos, lien pochette
- Pochette auto MusicBrainz/CAA + cache disque
- Téléversement manuel de pochette (connecté)
- Édition des champs principaux (connecté)

## Notes
- Tables attendues: `records` et `record_images` (schémas fournis).
- Les images sont servies via `/covers/<filename>` depuis `IMAGES_DIR`.


