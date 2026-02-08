# Deployment Guide

Full guide for deploying the Discord bot to a Linux server (e.g., a DigitalOcean droplet).

## Server Requirements

- Linux (Ubuntu 22.04+ recommended)
- 1 GB RAM minimum
- Docker and Docker Compose v2
- Git

## Step 1: Server Setup

SSH into your server and install Docker:

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Log out and back in for group changes to take effect
exit
```

## Step 2: Clone and Configure

```bash
git clone <your-repo-url> ~/DiscordBot
cd ~/DiscordBot

# Create data directory for persistent storage
sudo mkdir -p /opt/bot/data
sudo chown $USER:$USER /opt/bot/data

# Set up environment variables
cp .env.example .env
nano .env   # Fill in your API keys
```

## Step 3: Build and Run

```bash
docker compose up -d --build
```

## Step 4: Verify

```bash
# Check container status
docker ps

# Follow logs
docker logs -f discord-bot

# The bot should show "Logged on as <BotName>" in the logs
```

## Ongoing Management

```bash
# View logs
docker logs -f discord-bot

# Restart
docker compose restart

# Stop
docker compose down

# Update (after pushing changes to master)
git pull origin master
docker compose up -d --build

# View resource usage
docker stats discord-bot
```

## Data Persistence

The bot stores data in `/opt/bot/data/` on the host, mounted into the container. This includes:

- `news_notification.db` - SQLite database for news notification configs
- `bot_channels.json` - Channel IDs the bot listens to (optional)
- `news_channels.json` - Channel IDs for news notifications (optional)

Back up `/opt/bot/data/` periodically to avoid data loss.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Bot not connecting | Check `DISCORD_TOKEN` in `.env`. Make sure the bot is invited to your server. |
| Container exits immediately | Run `docker logs discord-bot` to see the error. Usually a missing env var. |
| Commands not showing up | Use `/sync` in Discord after the bot connects for the first time. |
| Permission errors on data dir | Run `sudo chown -R $USER:$USER /opt/bot/data` |
