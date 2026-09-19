# 🐋 Docker Guide

Ce guide explique comment utiliser Docker Compose pour lancer l'application de gestion hospitalière.

## 📋 Prérequis

- Docker Desktop installé (Windows, macOS) ou Docker Engine (Linux)
- Git (pour cloner le dépôt)

## 🚀 Démarrage rapide

1. **Cloner le dépôt :**
```bash
git clone <url-du-dépôt>
cd gestion_hopital
```

2. **Lancer tous les services :**
```bash
docker compose up -d
```

Cela va démarrer :
- **web** : Application Flask (http://localhost:5002)
- **mysql** : Base de données MySQL 8.0 (port 3306)
- **phpmyadmin** : Interface d'administration (http://localhost:8080)

3. **Vérifier que tout fonctionne :**
```bash
docker compose ps
docker compose logs web
```

## 🔧 Services

### Web (Application Flask)
- **Port** : 5002
- **URL** : http://localhost:5002
- **Variables d'environnement** :
  - `FLASK_ENV=production`
  - `DB_HOST=mysql`
  - `DB_USER=myuser`
  - `DB_PASSWORD=Azerty1234`
  - `DB_NAME=hopital_db`

### MySQL (Base de données)
- **Port** : 3306
- **Version** : 8.0
- **Utilisateur** : myuser / Azerty1234
- **Base de données** : hopital_db
- **Healthcheck** : Attend que MySQL soit prêt avant de démarrer l'application

### phpMyAdmin (Interface d'administration)
- **Port** : 8080
- **URL** : http://localhost:8080
- **Hôte** : mysql
- **Utilisateur** : root / Azerty1234

## 📦 Volumes Docker

L'application utilise des volumes Docker nommés pour éviter les problèmes de partage de fichiers sur Windows :
- `mysql_data` : Données MySQL persistantes
- `instance_data` : Logs et fichiers d'instance
- `uploads_data` : Fichiers uploadés

## 🔑 Accès par défaut

- **Administrateur** : admin@hopital.com / admin123
- **Médecin test** : jean.dupont@hopital.com / medecin123

⚠️ **Important** : Changez ces mots de passe après la première connexion !

## 🛠️ Commandes utiles

```bash
# Démarrer les services
docker compose up -d

# Arrêter les services
docker compose down

# Arrêter et supprimer les volumes (supprime les données)
docker compose down -v

# Voir les logs
docker compose logs web
docker compose logs mysql

# Recréer les conteneurs
docker compose up -d --force-recreate

# Reconstruire l'image web
docker compose build web
docker compose up -d
```

## 🔐 Variables d'environnement

Vous pouvez personnaliser la configuration en créant un fichier `.env` :

```env
SECRET_KEY=votre-cle-secrete-personnalisée
FLASK_ENV=production
DB_HOST=mysql
DB_USER=myuser
DB_PASSWORD=votre-mot-de-passe-mysql
DB_NAME=hopital_db
```

## 🐛 Résolution de problèmes

### Les conteneurs ne démarrent pas

```bash
# Vérifier les logs
docker compose logs

# Recréer les volumes
docker compose down -v
docker compose up -d
```

### Problème de connexion MySQL

Le service web attend automatiquement que MySQL soit prêt grâce au healthcheck. Attendez quelques secondes après le démarrage.

### Accès refusé sur Windows

Si vous avez des problèmes de partage de fichiers sur Windows, utilisez déjà les volumes Docker nommés (configurés par défaut).

## 📝 Note sur la sécurité

⚠️ **Pour la production** :
- Changez les mots de passe par défaut
- Utilisez des variables d'environnement sécurisées
- Configurez HTTPS avec un reverse proxy (Nginx)
- Utilisez des secrets Docker pour les mots de passe sensibles

## 🌐 Accès depuis le réseau

Pour accéder à l'application depuis d'autres machines sur le réseau, modifiez le port mapping dans `docker-compose.yml` :

```yaml
ports:
  - "0.0.0.0:5002:5002"  # Accepte les connexions de toutes les interfaces
```
