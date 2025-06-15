# Topic Manager Bot

Telegram bot for creating topics in a group.

## Installation

1. Clone the repository
2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # for Linux/macOS
# or
.\venv\Scripts\activate  # for Windows
```
3. Install dependencies:
```bash
pip install -r requirements.txt
```
4. Copy `.env.example` to `.env` and fill in the variables:
   - BOT_TOKEN - bot token from @BotFather
   - ADMIN_ID - bot administrator ID
   - TARGET_GROUP_ID - target group ID (negative value)

5. Run the bot:
```bash
python3 bot.py
```

## Usage

1. Add the bot to the target group
2. Make the bot an administrator of the group
3. Make sure the bot has permission to create topics
4. Use commands:
   - `/new10topics` - create 10 new topics
   - `/ids` - get current chat ID and your ID (useful for .env setup)

## Requirements
- Group must be a forum (have topics enabled)
- Bot must be a group administrator and have rights to create topics
- Only the bot administrator can create topics
- Bot only works in the specified target group 