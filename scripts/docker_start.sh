#!/bin/bash
# Docker startup script
# Runs migrations and optional seed data

set -e

echo "🚀 Starting OnTime ERP services..."

# Wait for database to be ready
echo "⏳ Waiting for database..."
until docker-compose exec -T postgres pg_isready -U erp_user -d erp_db > /dev/null 2>&1; do
  sleep 1
done

echo "✅ Database is ready"

# Run migrations
echo "📦 Running database migrations..."
docker-compose exec -T backend uv run alembic upgrade head

# Optional: Run seed data
if [ -f "scripts/seed_data.py" ]; then
    echo "🌱 Running seed data..."
    docker-compose exec -T backend python scripts/seed_data.py || echo "⚠️ Seed data script failed or not needed"
fi

# Health check
echo "🏥 Checking backend health..."
docker-compose exec -T backend curl -f http://localhost:8000/health || exit 1

echo "✅ All services started successfully!"

