# Discord Bot

A multi-purpose Discord bot with AI chat (GPT), news aggregation, stock/crypto price charts, Google Trends, and a natural language agent interface. Built with [discord.py](https://discordpy.readthedocs.io/) and organized in a layered Cog/BLL/Services architecture.

## How It Works

The bot uses a three-layer architecture:

- **Cogs** (`bot/cogs/`) - Discord command handlers. Each cog registers slash commands and hybrid commands with Discord. Cogs receive user input and pass it to the BLL layer. They never call external APIs directly.
- **BLL (Business Logic Layer)** (`bot/bll/`) - The middle layer that handles formatting, validation, and orchestration. It decides how to combine data from services and format responses (embeds, charts, text) for Discord.
- **Services** (`bot/services/`) - Thin wrappers around external APIs (OpenAI, yfinance, World News API, pytrends). Each service client handles authentication and raw API calls.

This separation means you can swap out an API (e.g., change news providers) by editing only the service layer without touching commands or business logic.

## Features

- **AI/GPT** - Chat with GPT-4 and GPT-3.5, generate images with DALL-E 3
- **Ava (Agent)** - Natural language interface that decides which bot functions to call using GPT tool calling
- **News** - Search and display news articles from AP, Reuters, BBC, NPR, CNN, Fox, Sky News (via World News API)
- **Finance** - Stock and crypto price charts with financial statement data (via yfinance)
- **Trends** - Google Trends real-time trending searches
- **Roles** - Self-service role selection via dropdown menus
- **Admin** - Command tree syncing
- **Misc** - Invite link generation

## Prerequisites

- Python 3.11+
- A Discord bot token ([how to create one - see below](#creating-a-discord-bot))
- An [OpenAI API key](https://platform.openai.com/api-keys)
- A [World News API key](https://worldnewsapi.com/)
- Docker (for deployment)

## Creating a Discord Bot

If you haven't created a Discord bot before, here's the full walkthrough:

### 1. Create a Discord Application

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **"New Application"** in the top right
3. Give it a name (this is the app name, not the bot username) and click **Create**

### 2. Create the Bot User

1. In your application, go to the **"Bot"** tab in the left sidebar
2. Click **"Add Bot"** and confirm
3. Under the bot's username, click **"Reset Token"** to generate a new token
4. **Copy the token** - this is your `DISCORD_TOKEN`. You won't be able to see it again.
5. Under **Privileged Gateway Intents**, enable:
   - **Message Content Intent** (required for the bot to read message content)

### 3. Invite the Bot to Your Server

1. Go to the **"OAuth2"** tab in the left sidebar
2. Under **OAuth2 URL Generator**, select these scopes:
   - `bot`
   - `applications.commands`
3. Under **Bot Permissions**, select:
   - Send Messages
   - Send Messages in Threads
   - Embed Links
   - Attach Files
   - Read Message History
   - Use Slash Commands
   - Manage Roles (if using the role selection feature)
   - Create Instant Invite (if using the invite command)
4. Copy the generated URL at the bottom and open it in your browser
5. Select your server from the dropdown and click **Authorize**

### 4. First Run

After starting the bot (see Quick Start below), run the `/sync` command in any channel the bot can see. This registers all slash commands with Discord. You only need to do this once, or again after adding new commands.

## Quick Start (Local Development)

```bash
# Clone the repo
git clone <your-repo-url>
cd DiscordBot

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Run the bot
python -m bot
```

## Docker Deployment

```bash
# Copy and fill in your API keys
cp .env.example .env
nano .env

# Build and run
docker compose up -d --build

# View logs
docker logs -f discord-bot
```

For full server/droplet setup instructions, see [docs/deployment.md](docs/deployment.md).

## Configuration

All configuration is through environment variables (set in `.env`):

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DISCORD_TOKEN` | Yes | - | Your Discord bot token |
| `OPENAI_API_KEY` | Yes | - | OpenAI API key for GPT and DALL-E |
| `WORLD_NEWS_API_KEY` | Yes | - | World News API key |
| `BOT_DATA_DIR` | No | `/opt/bot/data` | Directory for persistent data (SQLite DB, config files) |
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `COMMAND_PREFIX` | No | `!` | Prefix for text-based commands |

## Slash Commands

These commands are available after running `/sync`:

| Command | Description | Usage |
|---------|-------------|-------|
| `/gpt <prompt> [model]` | Chat with GPT. Models: GPT-4o (default), GPT-4o-mini, GPT-4-Turbo | `/gpt What is quantum computing?` |
| `/image <prompt>` | Generate an image with DALL-E 3 | `/image a sunset over mountains` |
| `/ava <prompt>` | Natural language agent - figures out what to do from your prompt using GPT tool calling | `/ava show me the latest tech news and AAPL stock price` |
| `/news [text] [n] [source]` | Get news articles. Optional: topic, count (max 6), source | `/news text:AI n:3 source:BBC` |
| `/notifications` | List active news notification loops for this server | `/notifications` |
| `/stop_news_notification <ids>` | Stop one or more news notification loops by ID | `/stop_news_notification 1 2` |
| `/ticker <tickers> [period]` | Stock/crypto price chart with embed. Up to 5 tickers. Periods: 1d, 5d, 1mo, 3mo, 6mo, 1y, 5y, max | `/ticker AAPL MSFT period:1mo` |
| `/trending` | Get current trending Google searches | `/trending` |
| `/roles` | Self-service role selection dropdown | `/roles` |
| `/invite` | Generate a permanent invite link for the current channel | `/invite` |
| `/sync` | Sync slash commands with Discord (run once after deploy) | `/sync` |

## Project Structure

```
DiscordBot/
├── bot/                        # Main package
│   ├── __main__.py             # Entry point (python -m bot)
│   ├── config.py               # Environment variable config + logging
│   ├── client.py               # Discord bot client, cog loader
│   ├── schemas/                # Static JSON configs
│   │   └── gpt.json            # GPT tool definitions for Ava agent
│   ├── cogs/                   # Discord command handlers
│   │   ├── ai.py               # /gpt, /image
│   │   ├── news.py             # /news, /notifications, /stop_news_notification
│   │   ├── trends.py           # /trending
│   │   ├── finance.py          # /ticker
│   │   ├── admin.py            # /sync
│   │   ├── interactions.py     # /roles
│   │   ├── ava.py              # /ava (natural language agent)
│   │   └── misc.py             # /invite
│   ├── bll/                    # Business logic layer
│   │   ├── ai.py               # GPT orchestration, cost tracking
│   │   ├── news.py             # News formatting, notification loops
│   │   ├── finance.py          # Chart generation, financial data
│   │   ├── trends.py           # Trends processing
│   │   ├── ava.py              # Agent: continuous tool calling loop
│   │   ├── admin.py            # Welcome message modal, role utils
│   │   ├── misc.py             # Invite link logic
│   │   └── ui/                 # Discord UI components
│   │       └── news_notification_setup.py
│   ├── services/               # External API wrappers
│   │   ├── openai_client.py    # OpenAI (GPT, DALL-E, Assistants)
│   │   ├── news_client.py      # World News API
│   │   ├── finance_client.py   # yfinance
│   │   ├── trends_client.py    # pytrends (Google Trends)
│   │   ├── task_manager.py     # In-memory singleton for notification tasks
│   │   └── warn_notice.py      # WARN Act layoff notices (Texas)
│   ├── database/
│   │   └── news_db.py          # SQLite for news notification configs
│   └── utils/
│       └── helpers.py          # Message chunking, theme colors, JSON I/O
├── deployment/                 # Deployment scripts
│   ├── README.md
│   ├── deploy/
│   │   └── deploy_bot.bash
│   ├── stop/
│   │   └── stop_bot.bash
│   └── rollback/
│       └── rollback_bot.bash
├── docs/
│   └── deployment.md           # Full server setup guide
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── .gitignore
```

## Adding a New Command

To add a new slash command (e.g., `/weather`):

1. **Create a service** (if calling an external API): `bot/services/weather_client.py`
2. **Create BLL logic**: `bot/bll/weather.py` - format data into Discord embeds
3. **Create a cog**: `bot/cogs/weather.py`:
   ```python
   from discord.ext import commands
   from discord import app_commands
   from bot.bll.weather import WeatherBll

   class Weather(commands.Cog):
       def __init__(self, bot):
           self.bot = bot
           self.weather = WeatherBll()

       @commands.hybrid_command(name="weather")
       @app_commands.describe(city="City name")
       async def weather(self, ctx, *, city: str):
           data = self.weather.get_weather(city)
           await ctx.reply(**data)
   ```
4. **Register in** `bot/client.py`:
   ```python
   from bot.cogs.weather import Weather
   # in load_cogs():
   await self.add_cog(Weather(self))
   ```
5. **Run `/sync`** in Discord to register the new command

## Deployment

See [deployment/README.md](deployment/README.md) for scripts and [docs/deployment.md](docs/deployment.md) for full server setup.
