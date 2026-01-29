#!/bin/bash

# Load configuration from .env file
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/.env"

# Use environment variables from .env
CONTAINER_NAME="$REDSHIFT_CONTAINER_NAME"
IMAGE_NAME="$REDSHIFT_IMAGE_NAME"
PORT="$REDSHIFT_PORT"

# Remove existing container if exists
if docker ps -a | grep -w "$CONTAINER_NAME" > /dev/null; then
    echo "Removing existing container: $CONTAINER_NAME"
    docker rm -f $CONTAINER_NAME
fi

echo "Starting Redshift Emulator (pgredshift) Docker container..."
docker run -d --name $CONTAINER_NAME \
  -p $PORT:5432 \
  -e POSTGRES_PASSWORD=$REDSHIFT_POSTGRES_PASSWORD \
  -e POSTGRES_USER=$REDSHIFT_POSTGRES_USER \
  -e POSTGRES_DB=$REDSHIFT_POSTGRES_DB \
  $IMAGE_NAME

# Wait a moment for the container to start
sleep 3

# Check if container is running
if docker ps | grep -w "$CONTAINER_NAME" > /dev/null; then
    echo "✅ pgredshift running successfully on localhost:$PORT"
    echo "Connection details:"
    echo "  Host: localhost"
    echo "  Port: $PORT"
    echo "  Database: $REDSHIFT_POSTGRES_DB"
    echo "  Username: $REDSHIFT_POSTGRES_USER"
    echo "  Password: $REDSHIFT_POSTGRES_PASSWORD"
else
    echo "❌ Container failed to start. Checking logs..."
    docker logs $CONTAINER_NAME
    exit 1
fi