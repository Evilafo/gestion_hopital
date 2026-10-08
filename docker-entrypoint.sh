#!/bin/bash
set -e

echo "⏳ Attente de la base de données MySQL..."
until python -c "import pymysql; pymysql.connect(host='$DB_HOST', user='$DB_USER', password='$DB_PASSWORD', db='$DB_NAME')" 2>/dev/null; do
    echo "   MySQL non disponible - attente..."
    sleep 2
done
echo "✅ MySQL est prêt !"

echo "📦 Exécution des migrations de base de données..."
flask db upgrade

# Peuplement optionnel - seulement si la variable d'environnement est définie
if [ "$SEED_DATABASE" = "true" ]; then
    echo "🌱 Peuplement de la base de données avec les données de test..."
    python scripts/seed_database.py
fi

echo "🚀 Démarrage de l'application..."
exec python run.py
