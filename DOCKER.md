# Docker Setup Guide

Complete guide for running the LLM Location Assistant with Docker.

## What's Included

The Docker Compose setup includes:
- **App Container**: FastAPI application
- **Ollama Container**: Local LLM service (Llama 3)
- **Persistent Storage**: LLM models are saved between restarts

## Prerequisites

- Docker Desktop or Docker Engine + Docker Compose
- At least 8GB RAM (for LLM models)
- 10GB free disk space (for Ollama models)

## Quick Start

### 1. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your Google Maps API key
# On Windows: notepad .env
# On Linux/Mac: nano .env
```

Required in `.env`:
```env
GOOGLE_MAPS_API_KEY=your_actual_api_key_here
LLM_MODEL=llama3
DEBUG=False
```

### 2. Start Services

```bash
# Start all containers in background
docker-compose up -d

# This will:
# - Download Ollama image (~2GB)
# - Build your app image
# - Start both containers
# - Create network and volumes
```

### 3. Download LLM Model

```bash
# Pull Llama 3 model (first time only, ~4.7GB)
docker exec -it llm-location-ollama ollama pull llama3

# Alternative models:
# docker exec -it llm-location-ollama ollama pull mistral
# docker exec -it llm-location-ollama ollama pull phi3
```

### 4. Verify Everything is Running

```bash
# Check container status
docker-compose ps

# Check app logs
docker-compose logs -f app

# Check health
curl http://localhost:8000/api/health
```

### 5. Access the Application

- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Ollama API**: http://localhost:11434

## Common Commands

### View Logs

```bash
# All services
docker-compose logs -f

# Only app
docker-compose logs -f app

# Only Ollama
docker-compose logs -f ollama
```

### Restart Services

```bash
# Restart everything
docker-compose restart

# Restart only app (after code changes)
docker-compose restart app
```

### Stop Services

```bash
# Stop containers (keeps volumes)
docker-compose down

# Stop and remove volumes (deletes downloaded models!)
docker-compose down -v
```

### Rebuild After Code Changes

```bash
# Rebuild and restart app
docker-compose up -d --build app

# Force rebuild from scratch
docker-compose build --no-cache app
docker-compose up -d
```

### Check Resource Usage

```bash
# See CPU/Memory usage
docker stats

# See disk usage
docker system df
```

## Managing LLM Models

### List Installed Models

```bash
docker exec -it llm-location-ollama ollama list
```

### Pull Additional Models

```bash
# Mistral (smaller, faster)
docker exec -it llm-location-ollama ollama pull mistral

# Phi-3 (very small, good for testing)
docker exec -it llm-location-ollama ollama pull phi3

# Llama 3.1 (newer version)
docker exec -it llm-location-ollama ollama pull llama3.1
```

### Switch Models

Edit `.env`:
```env
LLM_MODEL=mistral
```

Then restart:
```bash
docker-compose restart app
```

### Remove Models

```bash
# Remove a specific model
docker exec -it llm-location-ollama ollama rm mistral

# Check freed space
docker exec -it llm-location-ollama ollama list
```

## Troubleshooting

### Port Already in Use

If port 8000 or 11434 is already in use, edit `docker-compose.yml`:

```yaml
services:
  app:
    ports:
      - "8001:8000"  # Use 8001 on host instead

  ollama:
    ports:
      - "11435:11434"  # Use 11435 on host instead
```

Then update `.env`:
```env
LLM_BASE_URL=http://ollama:11434/v1  # Keep this, internal network
```

### Container Won't Start

```bash
# Check detailed logs
docker-compose logs app

# Check container status
docker ps -a

# Remove and recreate
docker-compose down
docker-compose up -d
```

### App Can't Connect to Ollama

Check if Ollama is running:
```bash
docker exec -it llm-location-ollama ollama list
```

If fails, check Ollama logs:
```bash
docker-compose logs ollama
```

### Out of Memory

Ollama needs RAM for models:
- Llama 3 (8B): ~8GB RAM
- Mistral: ~4GB RAM
- Phi-3: ~2GB RAM

Use smaller model if needed:
```bash
docker exec -it llm-location-ollama ollama pull phi3
```

Update `.env`:
```env
LLM_MODEL=phi3
```

### Slow Performance

1. Check if Docker has enough resources:
   - Docker Desktop → Settings → Resources
   - Increase CPU cores and memory

2. Use GPU acceleration (if available):
   Edit `docker-compose.yml`:
   ```yaml
   ollama:
     image: ollama/ollama:latest
     deploy:
       resources:
         reservations:
           devices:
             - driver: nvidia
               count: 1
               capabilities: [gpu]
   ```

## Production Deployment

### Security Hardening

1. **Use specific image versions**:
   ```yaml
   ollama:
     image: ollama/ollama:0.1.32  # Pin version
   ```

2. **Restrict CORS** in `app/main.py`:
   ```python
   allow_origins=["https://yourdomain.com"]
   ```

3. **Use secrets** instead of .env:
   ```yaml
   environment:
     - GOOGLE_MAPS_API_KEY_FILE=/run/secrets/gmaps_key
   secrets:
     - gmaps_key
   ```

4. **Add reverse proxy** (Nginx/Traefik)

### Environment Variables

```env
# Production settings
DEBUG=False
APP_HOST=0.0.0.0
APP_PORT=8000

# LLM settings
LLM_BASE_URL=http://ollama:11434/v1
LLM_MODEL=llama3

# Required
GOOGLE_MAPS_API_KEY=your_production_key
```

### Backup LLM Models

```bash
# Backup volume
docker run --rm -v llm-location_ollama_data:/data -v $(pwd):/backup \
  ubuntu tar czf /backup/ollama-models-backup.tar.gz /data

# Restore volume
docker run --rm -v llm-location_ollama_data:/data -v $(pwd):/backup \
  ubuntu tar xzf /backup/ollama-models-backup.tar.gz -C /
```

## Architecture

```
┌─────────────────────────────────────┐
│  Host Machine (localhost:8000)      │
└─────────────────┬───────────────────┘
                  │
        ┌─────────▼─────────┐
        │  llm-network      │
        │  (Docker Bridge)  │
        └─────────┬─────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
   ┌────▼────┐        ┌─────▼─────┐
   │   App   │────────│  Ollama   │
   │  :8000  │        │  :11434   │
   └─────────┘        └───────────┘
                            │
                      ┌─────▼─────┐
                      │  Volume   │
                      │ (Models)  │
                      └───────────┘
```

## Uninstall

```bash
# Stop and remove everything
docker-compose down -v

# Remove images
docker rmi llm-location-app ollama/ollama

# Clean up unused resources
docker system prune -a
```

## Next Steps

1. Configure Google Maps API key in `.env`
2. Start containers with `docker-compose up -d`
3. Pull LLM model
4. Open http://localhost:8000
5. Start chatting!
