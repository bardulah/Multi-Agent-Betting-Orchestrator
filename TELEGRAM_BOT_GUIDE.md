# Telegram Bot Guide - Mobile Access

Access the betting analysis system from your phone via Telegram Bot!

## Quick Start

### Prerequisites
- Telegram account
- Telegram Bot Token (configured in `config/.env`)
- Chat ID (your Telegram user ID)

### Step 1: Get Your Bot Token

1. Open Telegram and search for `@BotFather`
2. Send `/newbot`
3. Follow the prompts to create a new bot
4. Copy the token (format: `123456789:ABCdefGHIjklMNOpqrSTUvwxYZ1234567890`)

### Step 2: Configure Environment

Edit `config/.env` and add:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_user_id_here
```

To find your Chat ID:
1. Send any message to your bot
2. Go to: `https://api.telegram.org/botYOUR_TOKEN/getUpdates`
3. Look for `"chat":{"id":YOUR_ID}` in the response

### Step 3: Start the Bot

```bash
python3 telegram_bot.py
```

You should see:
```
INFO: Telegram Bot Handler initialized
INFO: Telegram bot is running. Press Ctrl+C to stop.
```

### Step 4: Use in Telegram

1. Open your bot in Telegram
2. Send `/start`
3. See the main menu with buttons

## Commands & Features

### Main Menu (/start)
Shows 4 main options:
- 📊 **Show Results** - View latest recommendations
- 🔍 **Analyze** - Run new analysis
- ⚙️ **Settings** - Configure preferences (coming soon)
- ❓ **Help** - Show available commands

### View Recommendations (/show)

**Flow:**
1. Tap "📊 Show Results"
2. Bot shows first recommendation with full details
3. Use pagination buttons to browse:
   - **◀️ Prev** - Previous bet
   - **📄 1/10** - Status (1st of 10 bets)
   - **Next ▶️** - Next bet

**Information Shown:**
- Match: Home Team vs Away Team
- Sport & League
- Match Time
- Recommended Pick & Odds
- Confidence Score
- Internet Picks Analysis
- Data-Driven Analysis

### Run Analysis (/analyze)

**Flow:**
1. Tap "🔍 Analyze"
2. Choose sport:
   - ⚽ **All Sports** - Analyze everything (5-15 min)
   - ⚽ **Football** - Football matches only (2-5 min)
   - 🏀 **Basketball** - Basketball matches only
   - 🎾 **Tennis** - Tennis matches only
   - 🏒 **Hockey** - Hockey matches only
3. Bot shows "Running Analysis..."
4. Bot updates when complete:
   - ✅ **Analysis Complete!** (success)
   - ❌ **Analysis Failed** (error)
5. Tap "📊 Show Results" to view new recommendations

**Time Estimates:**
- All Sports: 5-15 minutes
- Single Sport: 2-5 minutes
- Depends on: number of matches, API latency

### Help (/help)

Shows all available commands and quick examples:
- `/start` - Show main menu
- `/analyze` - Run analysis
- `/show` - View results
- `/help` - Show this message

## Architecture

```
Telegram Bot (telegram_bot.py)
├── BettingBotHandler
│   ├── Command Handlers
│   │   ├── /start - Welcome menu
│   │   ├── /help - Show commands
│   │   ├── /show - Display results
│   │   └── /analyze - Trigger analysis
│   │
│   └── Integration (bot_integration.py)
│       ├── ResultsLoader - Load matches & results
│       ├── ResultFormatter - Format for Telegram
│       ├── BetPaginator - Browse through bets
│       └── AnalysisRunner - Execute analysis
│
└── Runs 24/7 (polling Telegram servers)
```

## Folder Structure

```
/opt/deployment/repos/adk/
├── telegram_bot.py                 # Main bot
├── bot_integration.py              # Integration layer
├── TELEGRAM_BOT_GUIDE.md          # This file
├── test_telegram_bot.py           # Bot tests
├── test_telegram_show_command.py  # /show tests
├── run.py                          # Analysis entry point
├── config/
│   └── .env                        # TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
└── data/
    ├── results.json                # Today's analysis results
    ├── results-tomorrow.json       # Tomorrow's analysis results
    ├── matches.json                # Today's match data
    └── matches-tomorrow.json       # Tomorrow's match data
```

## Running as Background Service

### Option 1: Using nohup

```bash
# Start bot in background
nohup python3 telegram_bot.py > telegram_bot.log 2>&1 &

# View logs
tail -f telegram_bot.log

# Kill the bot
pkill -f telegram_bot.py
```

### Option 2: Using PM2

```bash
# Install PM2
npm install -g pm2

# Start bot
pm2 start telegram_bot.py --name "betting-bot" --interpreter python3

# View logs
pm2 logs betting-bot

# Restart
pm2 restart betting-bot

# Stop
pm2 stop betting-bot

# Auto-start on server reboot
pm2 startup
pm2 save
```

### Option 3: Using systemd

Create `/etc/systemd/system/betting-bot.service`:

```ini
[Unit]
Description=Multi-Agent Betting System Telegram Bot
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/opt/deployment/repos/adk
ExecStart=/usr/bin/python3 /opt/deployment/repos/adk/telegram_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable betting-bot
sudo systemctl start betting-bot
sudo systemctl status betting-bot
```

## Troubleshooting

### Bot Not Responding

**Check logs:**
```bash
tail -f telegram_bot.log  # if using nohup
pm2 logs betting-bot       # if using PM2
journalctl -u betting-bot  # if using systemd
```

**Common issues:**
- ❌ `TELEGRAM_BOT_TOKEN not found`
  - Solution: Add token to `config/.env`

- ❌ `Analysis failed with code 1`
  - Solution: Check `run.py` works: `python3 run.py`

- ❌ Bot not receiving messages
  - Solution: Verify token is correct in Telegram via BotFather

### Analysis Hangs

- Check server resources: `free -h`, `df -h`
- Check if analysis is running: `ps aux | grep run.py`
- Timeout is 1 hour - analysis should complete before then

### Bot Crashes

- Check system logs: `journalctl -n 50`
- Restart: `python3 telegram_bot.py`
- Consider using PM2 for auto-restart

## Testing

### Test Bot Locally

```bash
# Test initialization
python3 -c "from telegram_bot import BettingBotHandler; BettingBotHandler()"

# Run test suite
python3 test_telegram_bot.py

# Test /show command
python3 test_telegram_show_command.py
```

### Test Without Telegram

```bash
# Just test integration layer
python3 bot_integration.py

# Load results
python3 -c "from bot_integration import ResultsLoader; print(ResultsLoader().load_results())"
```

## Examples

### Example 1: Check Latest Results

1. Open Telegram
2. Send `/start` to bot
3. Tap "📊 Show Results"
4. View first recommendation
5. Use Prev/Next to browse

### Example 2: Run Analysis on Football

1. Send `/start`
2. Tap "🔍 Analyze"
3. Tap "⚽ Football"
4. Wait for "Running Analysis..."
5. Tap "📊 Show Results" when complete

### Example 3: Analyze Everything

1. Send `/start`
2. Tap "🔍 Analyze"
3. Tap "⚽ All Sports"
4. Wait 5-15 minutes
5. Results appear automatically

## Development

### Add New Command

1. Add handler method in `BettingBotHandler`
2. Add callback route in `button_callback()`
3. Add button in appropriate menu
4. Test with `test_telegram_bot.py`

Example:
```python
async def my_command_callback(self, update, context):
    query = update.callback_query
    await query.answer()

    message = "My command output"
    keyboard = [[InlineKeyboardButton("Back", callback_data="start_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode="HTML")
```

### Modify Result Display

Edit `ResultFormatter` methods in `bot_integration.py`:
- `format_recommendation_summary()` - Summary view
- `format_bet()` - Quick view of single bet
- `format_full_bet()` - Detailed view with reasoning

## Next Steps

Coming soon:
- ⏳ Settings command (/settings)
- ⏳ Filter recommendations by sport
- ⏳ Export results as CSV/PDF
- ⏳ Scheduled daily notifications
- ⏳ Web dashboard alternative

## Support

- Check logs for error messages
- Review `/help` command in bot
- See test output for debugging

## FAQ

**Q: How often should I run analysis?**
A: Daily or before betting. Run takes 2-15 min depending on sports.

**Q: Can multiple people use the same bot?**
A: Yes! Each user has their own chat_id and pagination state.

**Q: What if analysis fails?**
A: Bot shows error message. Check logs and try again. Old results still available.

**Q: Is my data stored?**
A: Only match data and recommendations in `data/` folder. No user data.

**Q: How do I stop the bot?**
A: Press Ctrl+C or use `pm2 stop betting-bot`

---

**Happy betting! 🤖📊🎯**
