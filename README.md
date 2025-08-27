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
SPOTIFY_CLIENT_ID=votre-client-id-spotify
SPOTIFY_CLIENT_SECRET=votre-client-secret-spotify
```

### 3. Configuration Spotify (optionnel)
Pour activer le player Spotify :
1. Créez une application sur [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Récupérez votre `Client ID` et `Client Secret`
3. Ajoutez-les à votre fichier `.env`
4. Le player apparaîtra automatiquement sur les pages de détail des albums disponibles

## Lancer avec Docker
```bash
docker compose up --build -d
```
Application: `http://<votre-serveur>:8888`

Montages hôte:
- `/srv/sqlite` (RO) → DB SQLite existante
- `/srv/retrofy_images` (RW) → stockage persistant des pochettes et favicons

## Variables d'environnement
- `DB_PATH` (défaut `/srv/sqlite/ma_base.sqlite`)
- `IMAGES_DIR` (défaut `/data/images`)
- `SECRET_KEY` (à personnaliser en prod)
- `ADMIN_USERNAME` (nom d'utilisateur admin)
- `ADMIN_PASSWORD_HASH` (hash bcrypt du mot de passe)
- `SPOTIFY_CLIENT_ID` (optionnel, pour l'intégration Spotify)
- `SPOTIFY_CLIENT_SECRET` (optionnel, pour l'intégration Spotify)

## Fonctionnalités
- Recherche: texte, artiste, année, genre
- **Page d'accueil** : 30 albums aléatoires avec pochettes
- Grille d'albums avec pochettes
- Détail: toutes les infos, lien pochette
- Pochette auto MusicBrainz/CAA + cache disque
- Téléversement manuel de pochette (connecté)
- Édition des champs principaux (connecté)
- **Authentification sécurisée** avec hachage bcrypt
- **🎵 Player Spotify intégré** pour écouter les albums disponibles
- **🎨 Favicon complet** avec support multi-plateformes

## Sécurité
- ✅ Mots de passe hachés avec bcrypt
- ✅ Variables d'environnement pour les secrets
- ✅ Sessions sécurisées
- ✅ Protection contre les attaques par force brute (limitation de session)

## Notes
- Tables attendues: `records` et `record_images` (schémas fournis).
- Les images sont servies via `/covers/<filename>` depuis `IMAGES_DIR`.
- Les favicons sont servis via `/favicon/<filename>` depuis `/srv/retrofy_images`.
- **IMPORTANT** : Changez les identifiants par défaut en production !

## Configuration Favicon
Placez vos fichiers favicon dans `/srv/retrofy_images/` sur votre serveur hôte :
- `favicon.ico` - Fallback pour tous les navigateurs
- `favicon-16x16.png` - Petite taille pour navigateurs modernes
- `favicon-32x32.png` - Taille standard pour navigateurs modernes
- `apple-touch-icon.png` - iOS Safari et appareils Apple
- `android-chrome-192x192.png` - Android Chrome et PWA
- `android-chrome-512x512.png` - Android Chrome haute résolution

**Note** : Le répertoire `/srv/retrofy_images` sur l'hôte est monté vers `/data/images` dans le conteneur Docker.


