#!/bin/sh
set -e

until PGPASSWORD=$POSTGRES_PASSWORD psql -h db -U $POSTGRES_USER -d $POSTGRES_DB -c '\q'; do
  echo "En attente de PostgreSQL..."
  sleep 2
done

echo "PostgreSQL est prêt !"
exec "$@"