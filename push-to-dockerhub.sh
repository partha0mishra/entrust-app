#!/bin/bash
# Script to tag and push Entrust images to Docker Hub

# Replace with your Docker Hub username
DOCKERHUB_USERNAME="kshitij001"

echo "Tagging images for Docker Hub..."
docker tag entrust-backend:latest ${DOCKERHUB_USERNAME}/entrust-backend:latest
docker tag entrust-frontend:latest ${DOCKERHUB_USERNAME}/entrust-frontend:latest

echo "Pushing backend image to Docker Hub..."
docker push ${DOCKERHUB_USERNAME}/entrust-backend:latest

echo "Pushing frontend image to Docker Hub..."
docker push ${DOCKERHUB_USERNAME}/entrust-frontend:latest

echo "Done! Images pushed to Docker Hub."
echo ""
echo "Your teammates can now run:"
echo "docker compose -f docker-compose.hub.yml up"
echo ""
echo "Or update docker-compose.hub.yml with your Docker Hub username first."

