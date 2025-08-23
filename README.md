# Retrofy

Application Spotify-like minimaliste basée sur Flask, connectée à une base SQLite existante, avec recherche, fiches détaillées, récupération automatique de pochettes via MusicBrainz/Cover Art Archive (sans clé API) et téléversement manuel (protégé par authentification). Tout tourne dans Docker et s'expose sur le port 8888.

## Prérequis serveur
- Docker et docker-compose installés
- Base SQLite existante montée sur l'hôte: `/srv/sqlite/ma_base.sqlite`

## Configuration de sécurité

### 1. Générer un mot de passe sécurisé
```bash
python generate_password.py
```
Suivez les instructions pour créer un hash de mot de passe sécurisé.

### 2. Configurer les variables d'environnement
Copiez `env.example` vers `.env` et configurez :
```bash
cp env.example .env
```

Éditez `.env` avec vos valeurs :
```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=votre-hash-bcrypt-ici
SECRET_KEY=votre-cle-secrete-aleatoire
```

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
- `ADMIN_USERNAME` (nom d'utilisateur admin)
- `ADMIN_PASSWORD_HASH` (hash bcrypt du mot de passe)

## Fonctionnalités
- Recherche: texte, artiste, année, genre
- Grille d'albums avec pochettes
- Détail: toutes les infos, lien pochette
- Pochette auto MusicBrainz/CAA + cache disque
- Téléversement manuel de pochette (connecté)
- Édition des champs principaux (connecté)
- **Authentification sécurisée** avec hachage bcrypt

## Sécurité
- ✅ Mots de passe hachés avec bcrypt
- ✅ Variables d'environnement pour les secrets
- ✅ Sessions sécurisées
- ✅ Protection contre les attaques par force brute (limitation de session)

## Notes
- Tables attendues: `records` et `record_images` (schémas fournis).
- Les images sont servies via `/covers/<filename>` depuis `IMAGES_DIR`.
- **IMPORTANT** : Changez les identifiants par défaut en production !


