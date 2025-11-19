# Multi-Agent Betting System

A sophisticated multi-agent system leveraging **Google's Agent Development Kit (ADK)** for automated sports betting analysis. The system scrapes match data, analyzes it from multiple perspectives using real ADK LlmAgent instances, and provides intelligent betting recommendations.

> **✨ Built with proper Google ADK** - Uses `google.adk.LlmAgent` and ADK's built-in `google_search` tool (FREE!)

## 🎯 Features

- **Automated Match Scraping**: Puppeteer-based scraper for Flashscore.com (football, basketball, tennis, hockey)
  - Scrape today's matches: `npm run scrape`
  - Scrape tomorrow's matches: `npm run scrape:future`
- **Date-Specific Analysis**: Analyze matches for any date without data loss
  - Keep separate files: `data/matches.json` (today) and `data/matches-tomorrow.json` (tomorrow)
- **Multi-Agent Analysis**:
  - Internet Picks Agent: Aggregates betting tips from online sources
  - Data-Driven Agent: Statistical analysis based on objective data
  - Synthesis Agent: Combines both analyses for final recommendations
- **Smart Notifications**: Email and Telegram support with detailed betting recommendations
- **Daily Scheduling**: Automated daily execution with cron-like scheduling
- **Comprehensive Logging**: Detailed logs for debugging and tracking
- **Historical Tracking**: Stores all recommendations for performance analysis

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Orchestrator                              │
│  (Coordinates all agents and workflow)                      │
│  - Routes match files by date                              │
│  - Manages scraper execution                               │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐   ┌──────────────┐   ┌──────────────┐
│   Scraper     │   │   Internet   │   │ Data-Driven  │
│   Agent       │   │   Picks      │   │   Agent      │
│  (Node.js)    │   │   Agent      │   │              │
└───────────────┘   └──────────────┘   └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
                    ┌──────────────┐
                    │  Synthesis   │
                    │    Agent     │
                    └──────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │ Notification │
                    │    Agent     │
                    └──────────────┘
```

### Date-Aware File Routing

The orchestrator uses date-specific match files to prevent data loss when scraping different dates:

```
--date today     →  data/matches.json          ← Default
                    (used by python run.py)

--date tomorrow  →  data/matches-tomorrow.json
                    (used by python run.py --date tomorrow)
```

**Scraper Output:**
- Both `npm run scrape` and `npm run scrape:future` initially output to `data/matches.json`
- The orchestrator copies the data to the appropriate date-specific file after scraping
- This prevents overwrites when switching between date-specific scraping

## 📋 Prerequisites

- **Python 3.8+**
- **Node.js 16+**
- **npm**
- **Google API Key** (for ADK/GenAI - get from [Google AI Studio](https://makersuite.google.com/app/apikey))
- **Email account** (for notifications) OR **Telegram Bot** (optional)

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd adk
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Node.js Dependencies

```bash
cd scraper
npm install
cd ..
```

### 4. Configure Environment Variables

```bash
cp config/.env.example config/.env
```

Edit `config/.env` and add your credentials:

```env
# Google API (REQUIRED - ADK includes FREE google_search tool!)
GOOGLE_API_KEY=your_google_api_key_here

# Email (for Gmail, use app password)
EMAIL_PASSWORD=your_email_app_password_here

# Telegram (optional)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here
```

### 5. Configure System Settings

Edit `config/config.yaml` to customize:
- Sports to analyze
- Notification preferences
- Confidence thresholds
- Scheduling times

## 🔧 Configuration

### Google API Setup

1. **Google API Key** (Required):
   - Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create an API key
   - Add to `.env` as `GOOGLE_API_KEY`

   > **💡 That's it!** ADK's built-in `google_search` tool is FREE and doesn't require Custom Search API setup!

### Email Setup (Gmail)

1. Enable 2-Factor Authentication
2. Generate an [App Password](https://myaccount.google.com/apppasswords)
3. Add to `config/config.yaml` and `.env`

### Telegram Setup

1. Create a bot using [@BotFather](https://t.me/botfather)
2. Get your bot token
3. Find your chat ID by messaging [@userinfobot](https://t.me/userinfobot)
4. Add credentials to `.env`

## 📖 Usage

### Run Once

Execute the betting system immediately:

```bash
# Analyze today's matches
python run.py

# Analyze tomorrow's matches
python run.py --date tomorrow
```

Or with custom config:

```bash
python run.py --config path/to/config.yaml
python run.py --config path/to/config.yaml --date tomorrow
```

### Test Notifications

Send a test notification to verify setup:

```bash
python run.py --test-notification
```

### Run with Scheduler

Start the daily scheduler:

```bash
python scheduler.py
```

This will:
- Run immediately on startup
- Execute daily at the configured time (default: 09:00)
- Keep running until stopped with Ctrl+C

### Run as Background Service (Linux)

Create a systemd service:

```bash
sudo nano /etc/systemd/system/betting-system.service
```

Add:

```ini
[Unit]
Description=Multi-Agent Betting System
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/adk
ExecStart=/usr/bin/python3 /path/to/adk/scheduler.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable betting-system
sudo systemctl start betting-system
sudo systemctl status betting-system
```

## 📊 Output

### Results Files

- `data/matches.json`: Today's scraped match data
- `data/matches-tomorrow.json`: Tomorrow's scraped match data
- `data/results.json`: Latest recommendations
- `data/history.json`: Historical recommendations
- `logs/betting_system.log`: System logs

### Date-Specific Files

The system maintains separate match files for each date to prevent overwrites:
- Run `npm run scrape` to populate `data/matches.json` (today)
- Run `npm run scrape:future` to populate `data/matches-tomorrow.json` (tomorrow)
- Run `python run.py --date today` to analyze today's matches (uses `data/matches.json`)
- Run `python run.py --date tomorrow` to analyze tomorrow's matches (uses `data/matches-tomorrow.json`)

### Recommendation Format

```json
{
  "match_id": "match_123",
  "homeTeam": "Team A",
  "awayTeam": "Team B",
  "sport": "football",
  "recommendation": "BET",
  "recommended_pick": "home_win",
  "recommended_odds": 2.10,
  "confidence": 0.75,
  "reasoning": "Both analyses agree with strong supporting evidence..."
}
```

## 🧪 Testing

### Test Individual Components

**Test Scraper:**
```bash
cd scraper
npm run scrape          # Scrapes today's matches
npm run scrape:future   # Scrapes tomorrow's matches
```

**Test Internet Picks Agent:**
```python
from agents.internet_picks_agent import InternetPicksAgent
agent = InternetPicksAgent(config)
result = agent.analyze_match(match_data)
```

**Test Notifications:**
```bash
python run.py --test-notification
```

## 🔍 How It Works

### 1. Match Scraping
The Puppeteer-based scraper navigates to Flashscore.com and extracts:
- Match details (teams, time, league)
- Available bookmaker odds
- Multiple sports (football, basketball, tennis, hockey)

### 2. Parallel Analysis
For each match, two agents work simultaneously:

**Internet Picks Agent:**
- Searches Google for betting tips and predictions
- Aggregates consensus from multiple sources
- Identifies popular picks and reasoning

**Data-Driven Agent:**
- Searches for statistics, form, injuries
- Analyzes head-to-head records
- Makes predictions based on objective data only

### 3. Synthesis & Decision
The Synthesis Agent:
- Compares both analyses
- Evaluates agreement/disagreement
- Assesses odds value
- Makes final BET or NO_BET recommendation
- Only recommends when confidence and value thresholds are met

### 4. Notification
Sends formatted notifications with:
- Match details
- Recommended picks and odds
- Confidence levels
- Reasoning for each recommendation

## ⚙️ Advanced Configuration

### Adjust Confidence Thresholds

In `config/config.yaml`:

```yaml
agents:
  synthesis:
    min_value_threshold: 1.05  # Minimum odds value
    confidence_threshold: 0.7  # Minimum confidence (0-1)
```

### Rate Limiting

Adjust scraper delays to avoid IP bans:

```yaml
scraper:
  rate_limit_delay: 2000  # milliseconds
```

### Sports Selection

Enable/disable sports:

```yaml
sports:
  - football
  - basketball
  # - tennis
  # - hockey
```

## 🐛 Troubleshooting

### Date-Specific Issues

**Problem**: Analyzing tomorrow's matches but getting today's data
- Ensure you ran `npm run scrape:future` before analyzing
- Check that `data/matches-tomorrow.json` exists and has data
- Verify with: `python run.py --date tomorrow`

**Problem**: Data overwrites when switching between dates
- Each date has its own file: `data/matches.json` (today) and `data/matches-tomorrow.json` (tomorrow)
- Scraping both dates in sequence is safe - no data loss

### Scraper Issues

**Problem**: Matches not found
- Flashscore may have changed their HTML structure
- Check browser console logs
- Update selectors in `scraper/src/flashscore-scraper.js`

**Problem**: Browser crashes
- Increase system resources
- Reduce concurrent matches being processed

**Problem**: Tomorrow's scraper gets today's date
- Future matches are automatically dated to tomorrow via the orchestrator
- Check `data/matches-tomorrow.json` to confirm dates

### API Issues

**Problem**: Google API errors
- Check API key validity
- Verify quota limits
- Ensure APIs are enabled in Google Cloud Console

**Problem**: Search results empty
- Verify Custom Search Engine is configured
- Check search engine ID

### Notification Issues

**Problem**: Email not sending
- Verify Gmail app password (not regular password)
- Check SMTP settings
- Ensure 2FA is enabled

**Problem**: Telegram not working
- Verify bot token
- Check chat ID
- Ensure bot is started (send `/start` to your bot)

## 📈 Performance Tracking

Track bet outcomes by manually updating `data/history.json` with results:

```json
{
  "timestamp": "2025-01-15T09:00:00",
  "recommendations": [...],
  "outcomes": {
    "match_id": {
      "result": "win",
      "actual_odds": 2.10,
      "profit": 11.00
    }
  }
}
```

## 🔒 Security & Responsible Betting

### Security
- Never commit `.env` file
- Rotate API keys regularly
- Use app-specific passwords
- Limit API quota to prevent abuse

### Responsible Betting
- This system provides analysis, not guarantees
- Always do your own research
- Never bet more than you can afford to lose
- Be aware of gambling addiction risks
- Use betting limits and self-exclusion tools

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## ⚠️ Disclaimer

This software is for educational and research purposes only. The creators are not responsible for any financial losses incurred through use of this system. Sports betting involves risk, and past performance does not guarantee future results. Always gamble responsibly and within your means.

## 🆘 Support

For issues and questions:
- Check the troubleshooting section
- Review logs in `logs/betting_system.log`
- Open an issue on GitHub

## 🗺️ Roadmap

- [ ] Web dashboard for viewing recommendations
- [ ] Machine learning for improved predictions
- [ ] More sports (esports, MMA, etc.)
- [ ] Live betting support
- [ ] Bankroll management system
- [ ] Performance analytics dashboard
- [ ] Mobile app
- [ ] Multi-language support

## 📚 Resources

- [Google GenAI Documentation](https://ai.google.dev/)
- [Puppeteer Documentation](https://pptr.dev/)
- [Flashscore.com](https://www.flashscore.com/)
- [Responsible Gambling](https://www.begambleaware.org/)
