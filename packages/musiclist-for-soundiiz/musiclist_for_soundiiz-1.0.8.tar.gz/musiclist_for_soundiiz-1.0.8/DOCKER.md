# 🐳 Docker Usage Guide

Run MusicList for Soundiiz in a consistent, isolated environment on any platform.

## 🚀 Quick Start

### Option 1: Using Docker CLI

```bash
# Build the image
docker build -t musiclist-for-soundiiz .

# Run with your music directory
docker run --rm \
  -v /path/to/your/music:/music:ro \
  -v $(pwd)/output:/output \
  musiclist-for-soundiiz \
  -i /music -o /output/playlist.csv
```

### Option 2: Using Docker Compose (Recommended)

```bash
# Edit docker-compose.yml to set your music path
# Then run:
docker-compose run --rm musiclist -i /music -o /output/playlist.csv
```

## 📋 Prerequisites

- Docker installed ([Get Docker](https://docs.docker.com/get-docker/))
- Optional: Docker Compose ([Install Compose](https://docs.docker.com/compose/install/))

## 🔨 Building the Image

```bash
# Clone the repository
git clone https://github.com/lucmuss/musiclist-for-soundiiz.git
cd musiclist-for-soundiiz

# Build the Docker image
docker build -t musiclist-for-soundiiz .
```

## 💡 Usage Examples

### Basic CSV Export

```bash
docker run --rm \
  -v /home/user/Music:/music:ro \
  -v $(pwd)/output:/output \
  musiclist-for-soundiiz \
  -i /music -o /output/my_music.csv
```

### JSON Export with Duplicate Removal

```bash
docker run --rm \
  -v /home/user/Music:/music:ro \
  -v $(pwd)/output:/output \
  musiclist-for-soundiiz \
  -i /music \
  -o /output/clean_playlist.json \
  -f json \
  --remove-duplicates \
  --max-songs-per-file 500
```

### Multiple Directories

```bash
docker run --rm \
  -v /home/user/Music:/music1:ro \
  -v /mnt/external/Music:/music2:ro \
  -v $(pwd)/output:/output \
  musiclist-for-soundiiz \
  -i /music1 /music2 \
  -o /output/combined.csv
```

### Verbose Mode

```bash
docker run --rm \
  -v /home/user/Music:/music:ro \
  -v $(pwd)/output:/output \
  musiclist-for-soundiiz \
  -i /music -o /output/playlist.csv -v
```

## 🎯 Docker Compose Examples

### Edit docker-compose.yml

```yaml
version: '3.8'

services:
  musiclist:
    build: .
    image: musiclist-for-soundiiz:latest
    volumes:
      - /home/user/Music:/music:ro        # Your music directory
      - ./output:/output                  # Output directory
    command: -i /music -o /output/playlist.csv
```

### Run with Docker Compose

```bash
# Basic run
docker-compose run --rm musiclist

# With custom options
docker-compose run --rm musiclist -i /music -o /output/playlist.json -f json

# Remove duplicates
docker-compose run --rm musiclist -i /music -o /output/clean.csv --remove-duplicates

# Verbose output
docker-compose run --rm musiclist -i /music -o /output/playlist.csv -v
```

## 🔧 Advanced Usage

### Interactive Shell

Access the container for debugging or exploration:

```bash
docker run --rm -it \
  -v /home/user/Music:/music:ro \
  -v $(pwd)/output:/output \
  --entrypoint /bin/bash \
  musiclist-for-soundiiz
```

### Custom Python Script

```bash
docker run --rm -it \
  -v /home/user/Music:/music:ro \
  -v $(pwd)/output:/output \
  -v $(pwd)/my_script.py:/app/my_script.py \
  --entrypoint python \
  musiclist-for-soundiiz \
  /app/my_script.py
```

### Override Entrypoint

```bash
docker run --rm \
  -v /home/user/Music:/music:ro \
  --entrypoint python \
  musiclist-for-soundiiz \
  -m musiclist_for_soundiiz.cli --help
```

## 📁 Volume Mounts

### Input Directory (Music)

```bash
-v /path/to/music:/music:ro
```

- `:ro` = read-only (recommended for safety)
- Mount your music library here

### Output Directory

```bash
-v /path/to/output:/output
```

- Writable directory for generated files
- Use `$(pwd)/output` for current directory

### Multiple Music Directories

```bash
-v /music/rock:/music/rock:ro \
-v /music/pop:/music/pop:ro \
-v /music/jazz:/music/jazz:ro
```

Then use: `-i /music/rock /music/pop /music/jazz`

## 🌐 Platform-Specific Instructions

### Windows (PowerShell)

```powershell
docker run --rm `
  -v C:\Users\YourName\Music:/music:ro `
  -v ${PWD}\output:/output `
  musiclist-for-soundiiz `
  -i /music -o /output/playlist.csv
```

### Windows (CMD)

```cmd
docker run --rm ^
  -v C:\Users\YourName\Music:/music:ro ^
  -v %cd%\output:/output ^
  musiclist-for-soundiiz ^
  -i /music -o /output/playlist.csv
```

### macOS

```bash
docker run --rm \
  -v ~/Music:/music:ro \
  -v $(pwd)/output:/output \
  musiclist-for-soundiiz \
  -i /music -o /output/playlist.csv
```

### Linux

```bash
docker run --rm \
  -v /home/$USER/Music:/music:ro \
  -v $(pwd)/output:/output \
  musiclist-for-soundiiz \
  -i /music -o /output/playlist.csv
```

## 🐋 Docker Hub (Future)

Once published to Docker Hub:

```bash
# Pull from Docker Hub
docker pull lucmuss/musiclist-for-soundiiz:latest

# Run directly
docker run --rm \
  -v /path/to/music:/music:ro \
  -v $(pwd)/output:/output \
  lucmuss/musiclist-for-soundiiz \
  -i /music -o /output/playlist.csv
```

## 📊 Image Information

```bash
# View image details
docker images musiclist-for-soundiiz

# Inspect image
docker inspect musiclist-for-soundiiz

# View image layers
docker history musiclist-for-soundiiz
```

## 🔍 Troubleshooting

### Permission Issues

If you get permission errors on output files:

```bash
# Linux/macOS: Run with user ID
docker run --rm \
  --user $(id -u):$(id -g) \
  -v /path/to/music:/music:ro \
  -v $(pwd)/output:/output \
  musiclist-for-soundiiz \
  -i /music -o /output/playlist.csv
```

### Container Won't Start

```bash
# Check logs
docker logs musiclist-soundiiz

# Debug with shell
docker run --rm -it --entrypoint /bin/bash musiclist-for-soundiiz
```

### Volume Not Mounting

```bash
# Verify volumes
docker run --rm -v /path/to/music:/music alpine ls -la /music

# Check permissions
ls -la /path/to/music
```

## 🧹 Cleanup

### Remove Container

```bash
docker rm musiclist-soundiiz
```

### Remove Image

```bash
docker rmi musiclist-for-soundiiz
```

### Clean All

```bash
# Remove containers, images, and volumes
docker-compose down --rmi all --volumes

# Or manually
docker system prune -a
```

## 🎨 Benefits of Docker

✅ **Consistency** - Same environment everywhere  
✅ **Isolation** - No conflicts with system packages  
✅ **Portability** - Works on Windows, macOS, Linux  
✅ **No Installation** - No Python/pip setup required  
✅ **Clean** - No leftover files on host system  
✅ **Version Control** - Pin specific versions  

## 💻 CI/CD Integration

### GitHub Actions

```yaml
- name: Build Docker image
  run: docker build -t musiclist-for-soundiiz .

- name: Process music files
  run: |
    docker run --rm \
      -v ${{ github.workspace }}/music:/music:ro \
      -v ${{ github.workspace }}/output:/output \
      musiclist-for-soundiiz \
      -i /music -o /output/playlist.csv
```

### GitLab CI

```yaml
docker-build:
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t musiclist-for-soundiiz .
    - docker run --rm -v $(pwd)/music:/music:ro musiclist-for-soundiiz -i /music
```

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Best Practices](https://docs.docker.com/develop/dev-best-practices/)

## 🤝 Contributing

To build and test locally:

```bash
# Build development image
docker build -t musiclist-dev .

# Run tests in container
docker run --rm musiclist-dev pytest

# Development with live code
docker run --rm -it \
  -v $(pwd)/src:/app/src \
  musiclist-dev \
  /bin/bash
```

---

**Happy containerizing! 🐳🎵**
