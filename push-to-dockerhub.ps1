# PowerShell script to tag and push Entrust images to Docker Hub

# Replace with your Docker Hub username
$DOCKERHUB_USERNAME = "kshitij001"

Write-Host "Tagging images for Docker Hub..."
docker tag entrust-backend:latest "${DOCKERHUB_USERNAME}/entrust-backend:latest"
docker tag entrust-frontend:latest "${DOCKERHUB_USERNAME}/entrust-frontend:latest"

Write-Host "Pushing backend image to Docker Hub..."
docker push "${DOCKERHUB_USERNAME}/entrust-backend:latest"

Write-Host "Pushing frontend image to Docker Hub..."
docker push "${DOCKERHUB_USERNAME}/entrust-frontend:latest"

Write-Host "Done! Images pushed to Docker Hub."
Write-Host ""
Write-Host "Your teammates can now run:"
Write-Host "docker compose -f docker-compose.hub.yml up"
Write-Host ""
Write-Host "Or update docker-compose.hub.yml with your Docker Hub username first."

