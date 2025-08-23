# 🎵 Configuration Spotify pour Retrofy

Ce guide vous explique comment configurer l'intégration Spotify pour afficher un player sur les pages de détail des albums.

## 📋 Prérequis

1. Un compte Spotify (gratuit ou premium)
2. Accès au [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)

## 🔧 Configuration étape par étape

### 1. Créer une application Spotify

1. Allez sur [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Connectez-vous avec votre compte Spotify
3. Cliquez sur **"Create App"**
4. Remplissez les informations :
   - **App name** : `Retrofy` (ou le nom de votre choix)
   - **App description** : `Application de gestion de collection vinyle avec intégration Spotify`
   - **Website** : `http://localhost:8888` (pour le développement)
   - **Redirect URI** : `http://localhost:8888/callback` (optionnel)
5. Acceptez les conditions d'utilisation
6. Cliquez sur **"Save"**

### 2. Récupérer les identifiants

1. Sur la page de votre application, vous verrez :
   - **Client ID** : Une chaîne de caractères
   - **Client Secret** : Cliquez sur **"Show Client Secret"** pour le voir

2. Notez ces deux valeurs, elles seront nécessaires pour la configuration.

### 3. Configurer Retrofy

1. Copiez le fichier d'exemple :
   ```bash
   cp env.example .env
   ```

2. Éditez le fichier `.env` et ajoutez vos identifiants Spotify :
   ```env
   SPOTIFY_CLIENT_ID=votre-client-id-ici
   SPOTIFY_CLIENT_SECRET=votre-client-secret-ici
   ```

3. Redémarrez l'application :
   ```bash
   docker compose down
   docker compose up --build -d
   ```

## 🎯 Fonctionnalités

Une fois configuré, le player Spotify apparaîtra automatiquement :

- ✅ **Sur les pages de détail des albums** disponibles sur Spotify
- ✅ **Player intégré** avec contrôles de lecture
- ✅ **Lien direct** vers Spotify
- ✅ **Design cohérent** avec le thème de l'application
- ✅ **Gestion d'erreur** si l'album n'est pas trouvé

## 🔍 Comment ça fonctionne

1. **Recherche automatique** : Quand vous visitez une page de détail d'album, Retrofy recherche automatiquement l'album sur Spotify
2. **Affichage conditionnel** : Le player n'apparaît que si l'album est trouvé
3. **Player intégré** : Utilise l'API d'intégration officielle de Spotify
4. **Performance optimisée** : Les recherches sont faites à la demande

## 🛠️ Dépannage

### Le player n'apparaît pas

1. **Vérifiez vos identifiants** :
   ```bash
   python test_spotify_integration.py
   ```

2. **Vérifiez les logs** :
   ```bash
   docker compose logs retrofy
   ```

3. **Testez manuellement** :
   - Assurez-vous que l'album existe sur Spotify
   - Vérifiez que l'artiste et le titre correspondent exactement

### Erreurs d'API

- **Rate limiting** : Spotify limite les requêtes, attendez quelques minutes
- **Identifiants invalides** : Vérifiez votre Client ID et Secret
- **Réseau** : Vérifiez votre connexion internet

## 🔒 Sécurité

- Les identifiants Spotify sont stockés dans les variables d'environnement
- Aucune donnée personnelle n'est transmise à Spotify
- L'API utilise l'authentification Client Credentials (sans accès aux comptes utilisateurs)

## 📱 Utilisation

1. Naviguez vers une page de détail d'album
2. Si l'album est disponible sur Spotify, le player apparaîtra sous l'image
3. Utilisez les contrôles du player pour écouter
4. Cliquez sur "Ouvrir dans Spotify" pour aller sur l'application Spotify

## 🎨 Personnalisation

Le player utilise le thème officiel de Spotify et s'intègre parfaitement au design de Retrofy. Les styles CSS peuvent être modifiés dans `static/styles.css` si nécessaire.

---

**Note** : Cette fonctionnalité est optionnelle. Si vous ne configurez pas Spotify, l'application fonctionnera normalement sans le player.
