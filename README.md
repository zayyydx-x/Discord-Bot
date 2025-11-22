# Discord Bot

Small Discord bot using `discord.py` with basic moderation, fun, and utility commands.

Getting started

- Create a Python 3.10+ virtual environment and activate it.
- Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

- Create a `.env` file containing your bot token:

```
DISCORD_TOKEN=your-bot-token-here
```

- Run the bot:

```powershell
python d:\Bot\bot.py
```

Committing changes

```powershell
git add .
git commit -m "Small updates: logging, requirements, README, gitignore"
git push origin main
```

If you want me to create a branch, run tests, or make additional changes, tell me what to update next.
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

**Contributing**

- Fork the repository and create a branch for your change: `git checkout -b my-feature`.
- Make small, focused commits and add a brief commit message describing the change.
- Push your branch and open a pull request from your fork to the `enhance-documentation` branch.
- Keep PRs small and focused (one logical change per PR) to speed review.

Thank you for contributing — feel free to open issues or PRs for improvements.
