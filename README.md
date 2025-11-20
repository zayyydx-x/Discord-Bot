# Discord Bot

Files:

- `bot.py` - Main bot script (place your token in `.env` or set `DISCORD_TOKEN` env var).
- `.env.example` - Example environment file.
- `requirements.txt` - Python dependencies.

Quick start (PowerShell):

```powershell
cd d:\Bot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
# Create a .env file (copy from .env.example) and set your token
# Then run:
python bot.py
```

Notes:
- The bot requires a valid Discord bot token set as `DISCORD_TOKEN` in environment or in a `.env` file.
- Running the bot will connect to Discord — do not run without a valid token and correct permissions.
