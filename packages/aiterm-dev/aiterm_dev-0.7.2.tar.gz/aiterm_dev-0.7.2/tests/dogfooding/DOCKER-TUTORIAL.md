# Docker Tutorial for Beginners: Running aiterm Tests

A beginner-friendly guide to using Docker for running aiterm's Ghostty configuration tests.

## What is Docker?

**Docker** is a tool that packages applications and their dependencies into **containers** - lightweight, isolated environments that run consistently anywhere.

**Think of it like this:**

- 🏠 **Virtual Machine** = Entire house (heavy, slow)
- 📦 **Docker Container** = Shipping container (light, fast, portable)

## Why Use Docker for Testing?

✅ **Clean Environment**: Tests run in isolation, no conflicts with your system  
✅ **Reproducible**: Same results every time, on any computer  
✅ **No Installation Mess**: Test dependencies stay in the container  
✅ **Easy Cleanup**: Delete the container when done

## Prerequisites

### 1. Install Docker Desktop

**macOS:**

```bash
# Download from Docker website
open https://www.docker.com/products/docker-desktop

# Or install with Homebrew
brew install --cask docker
```

**After installation:**

1. Open Docker Desktop from Applications
2. Wait for "Docker Desktop is running" message
3. You'll see a whale icon in your menu bar

### 2. Verify Installation

```bash
# Check Docker is running
docker --version
# Output: Docker version 24.x.x

# Test Docker works
docker run hello-world
# Should download and run a test container
```

## Core Docker Concepts

### Images vs Containers

```
📋 Image (Blueprint)          🏃 Container (Running Instance)
├─ Recipe for environment     ├─ Active environment
├─ Stored on disk            ├─ Running in memory
└─ Build once                └─ Run many times
```

### Basic Docker Commands

| Command | What It Does | Example |
|---------|--------------|---------|
| `docker build` | Create an image from Dockerfile | `docker build -t myapp .` |
| `docker run` | Start a container from image | `docker run -it myapp` |
| `docker ps` | List running containers | `docker ps` |
| `docker stop` | Stop a running container | `docker stop myapp` |
| `docker rm` | Remove a container | `docker rm myapp` |
| `docker images` | List all images | `docker images` |
| `docker rmi` | Remove an image | `docker rmi myapp` |

### Important Flags

- `-it` = Interactive terminal (you can type commands)
- `--rm` = Auto-remove container when it stops
- `-v` = Mount a volume (share files with container)
- `-e` = Set environment variable

## Tutorial: Running the Ghostty Test

### Step 1: Navigate to Test Directory

```bash
cd /Users/dt/projects/dev-tools/aiterm/tests/dogfooding
```

### Step 2: Understanding the Files

**Dockerfile.ghostty** - Blueprint for the test environment

```dockerfile
FROM python:3.11-slim    # Start with Python 3.11
COPY . /app              # Copy aiterm code
RUN pip install -e .     # Install aiterm
CMD ["/usr/local/bin/test-ghostty"]  # Run test
```

**docker-compose.ghostty.yml** - Easy way to run Docker

```yaml
services:
  ghostty-test:          # Service name
    build: ...           # How to build
    volumes: ...         # What to share
    command: ...         # What to run
```

### Step 3: Run with Docker Compose (Easiest)

```bash
# Build and run in one command
docker-compose -f docker-compose.ghostty.yml up --build

# What happens:
# 1. Docker builds the image (first time only, ~2 min)
# 2. Creates a container
# 3. Runs the test script
# 4. Shows test results
```

**Expected Output:**

```
╔════════════════════════════════════════════════════════════╗
║  aiterm Ghostty Config Dogfooding Test                    ║
╚════════════════════════════════════════════════════════════╝

[TEST 1] Detect Ghostty terminal
  ✓ PASS
[TEST 2] Show Ghostty version
  ✓ PASS
...
```

### Step 4: Clean Up

```bash
# Stop and remove containers + volumes
docker-compose -f docker-compose.ghostty.yml down -v

# Remove the built image (optional)
docker rmi aiterm-ghostty-test
```

## Alternative: Run with Docker Directly

### Build the Image

```bash
# From project root
docker build -f tests/dogfooding/Dockerfile.ghostty -t aiterm-ghostty-test .

# Breakdown:
# -f = Use this Dockerfile
# -t = Tag (name) the image
# .  = Build context (current directory)
```

### Run the Container

```bash
# Run interactively
docker run -it --rm aiterm-ghostty-test

# Breakdown:
# -it = Interactive terminal
# --rm = Remove container after exit
# aiterm-ghostty-test = Image name
```

### Run with Development Mode

```bash
# Mount source code for live changes
docker run -it --rm \
  -v $(pwd):/app \
  -e TERM_PROGRAM=ghostty \
  aiterm-ghostty-test

# Breakdown:
# -v $(pwd):/app = Share current directory with container
# -e = Set environment variable
```

## Debugging Tips

### Enter Container Shell

```bash
# Run bash instead of test
docker run -it --rm aiterm-ghostty-test /bin/bash

# Now you're inside the container!
# Try commands manually:
ait ghostty status
ait ghostty config
cat /root/.config/ghostty/config
```

### View Container Logs

```bash
# List all containers (including stopped)
docker ps -a

# View logs from a container
docker logs <container-id>
```

### Check What's Running

```bash
# See running containers
docker ps

# See all images
docker images

# See disk usage
docker system df
```

## Common Issues

### "Cannot connect to Docker daemon"

**Problem:** Docker Desktop isn't running

**Solution:**

```bash
# Start Docker Desktop
open -a Docker

# Wait for whale icon in menu bar
# Try command again
```

### "Port already in use"

**Problem:** Another container using the same port

**Solution:**

```bash
# Stop all containers
docker stop $(docker ps -q)

# Or use different port
docker run -p 8081:8080 myapp
```

### "No space left on device"

**Problem:** Too many old images/containers

**Solution:**

```bash
# Remove unused containers
docker container prune

# Remove unused images
docker image prune

# Remove everything unused
docker system prune -a
```

## Best Practices

1. **Always use `--rm`** for temporary containers
2. **Tag your images** with meaningful names
3. **Clean up regularly** with `docker system prune`
4. **Use `.dockerignore`** to exclude unnecessary files
5. **Keep images small** - use slim base images

## Next Steps

### Learn More

- 📚 [Official Docker Tutorial](https://docs.docker.com/get-started/)
- 🎥 [Docker in 100 Seconds](https://www.youtube.com/watch?v=Gjnup-PuquQ)
- 📖 [Docker Compose Docs](https://docs.docker.com/compose/)

### Practice

Try modifying the test:

1. Edit `ghostty-config-test.sh`
2. Add a new test case
3. Rebuild and run: `docker-compose up --build`

### Advanced Topics

- Multi-stage builds for smaller images
- Docker networks for container communication
- Volume management for persistent data
- CI/CD integration with GitHub Actions

## Quick Reference Card

```bash
# Build
docker build -t name .

# Run (interactive)
docker run -it --rm name

# Run (background)
docker run -d name

# Stop
docker stop <id>

# Remove
docker rm <id>

# Clean up
docker system prune

# Compose
docker-compose up --build
docker-compose down -v
```

## Summary

**Docker lets you:**

- ✅ Run tests in clean, isolated environments
- ✅ Ensure consistent results across machines
- ✅ Avoid "works on my machine" problems
- ✅ Clean up easily when done

**For aiterm Ghostty tests:**

```bash
cd tests/dogfooding
docker-compose -f docker-compose.ghostty.yml up --build
```

That's it! You're now ready to use Docker for testing. 🐳
