# Deployment

## Prerequisites

- SSH access to your server
- Docker and Docker Compose installed on the server
- Git installed on the server
- The repo cloned on the server at `~/DiscordBot`
- A `.env` file on the server at `~/DiscordBot/.env` (copy from `.env.example`)

## SSH Config Setup

Add an entry to `~/.ssh/config` on your local machine:

```
Host discord-bot
    HostName <your-ip>
    User <your-user>
    IdentityFile ~/.ssh/<your-key>
```

## Scripts

| Script | Description |
|--------|-------------|
| `deploy/deploy_bot.bash` | Push to master, pull on server, rebuild and start container |
| `stop/stop_bot.bash` | Stop the running bot container |
| `rollback/rollback_bot.bash` | Roll back to a previous commit and rebuild |

## Usage

All deploys go from master. Merge your changes to master first, then run the deploy script.

```bash
# Deploy latest master
bash deployment/deploy/deploy_bot.bash

# Stop the bot
bash deployment/stop/stop_bot.bash

# Rollback to previous commit
bash deployment/rollback/rollback_bot.bash
```

## First-Time Server Setup

1. SSH into your server
2. Install Docker: follow [Docker's official guide](https://docs.docker.com/engine/install/)
3. Clone the repo: `git clone <your-repo-url> ~/DiscordBot`
4. Create data directory: `sudo mkdir -p /opt/bot/data && sudo chown $USER:$USER /opt/bot/data`
5. Copy and fill in environment: `cp .env.example .env && nano .env`
6. Build and start: `docker compose up -d --build`
7. Check logs: `docker logs -f discord-bot`
