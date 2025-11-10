# Quick Start Guide

Get up and running with the Multi-Agent Betting System in 5 minutes!

## 🚀 Quick Setup

### 1. Run Setup Script

```bash
chmod +x setup.sh
./setup.sh
```

This will:
- Check prerequisites (Python, Node.js, npm)
- Install all dependencies
- Create configuration files
- Set up directories

### 2. Configure API Keys

Edit `config/.env`:

```env
# Get from: https://makersuite.google.com/app/apikey
GOOGLE_API_KEY=your_key_here

# Get from: https://programmablesearchengine.google.com/
GOOGLE_SEARCH_ENGINE_ID=your_id_here

# For Gmail: https://myaccount.google.com/apppasswords
EMAIL_PASSWORD=your_app_password_here

# For Telegram: @BotFather
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

### 3. Configure Email/Telegram

Edit `config/config.yaml`:

```yaml
notifications:
  enabled: true
  method: "email"  # or "telegram" or "both"

  email:
    sender_email: "your-email@gmail.com"
    recipient_email: "recipient@example.com"
```

### 4. Test the System

```bash
# Test notification
python run.py --test-notification

# Run full system once
python run.py
```

### 5. Start Daily Scheduler

```bash
python scheduler.py
```

## ⚡ Minimal Setup (No Notifications)

If you just want to test the system without notifications:

1. Run `./setup.sh`
2. Add only `GOOGLE_API_KEY` to `config/.env`
3. Disable notifications in `config/config.yaml`:
   ```yaml
   notifications:
     enabled: false
   ```
4. Run: `python run.py`

Results will be saved to `data/results.json`.

## 🎯 Understanding the Output

After running, check:

- **Logs**: `logs/betting_system.log`
- **Latest Results**: `data/results.json`
- **Match Data**: `data/matches.json`
- **History**: `data/history.json`

### Example Result

```json
{
  "recommendation": "BET",
  "homeTeam": "Team A",
  "awayTeam": "Team B",
  "recommended_pick": "home_win",
  "recommended_odds": 2.10,
  "confidence": 0.75,
  "reasoning": "Strong agreement between analyses..."
}
```

## 🔧 Common Issues

### Scraper Not Working
```bash
cd scraper
npm install
npm run scrape
```

### Python Import Errors
```bash
pip install -r requirements.txt
```

### API Key Issues
- Verify keys in `config/.env`
- Check Google Cloud Console quotas
- Ensure APIs are enabled

## 📖 Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Customize settings in `config/config.yaml`
- Set up as a background service (see README.md)
- Add more sports or customize agents

## 🆘 Need Help?

Check:
1. `logs/betting_system.log` for errors
2. [README.md](README.md) troubleshooting section
3. GitHub issues

## ⚠️ Important Reminders

- This is for educational purposes
- Always bet responsibly
- Never bet more than you can afford to lose
- Do your own research before betting
- Past performance doesn't guarantee future results

Happy analyzing! 🎲
