# Project Structure

```
adk/
├── README.md                       # Main documentation
├── QUICKSTART.md                   # Quick start guide
├── LICENSE                         # MIT License
├── PROJECT_STRUCTURE.md            # This file
├── requirements.txt                # Python dependencies
├── setup.sh                        # Setup script
├── run.py                          # Main entry point
├── scheduler.py                    # Daily scheduler
├── .gitignore                      # Git ignore rules
│
├── config/                         # Configuration files
│   ├── config.yaml                 # Main configuration
│   └── .env.example                # Environment variables template
│
├── agents/                         # Python ADK agents
│   ├── __init__.py
│   ├── internet_picks_agent.py     # Internet betting tips agent
│   ├── data_driven_agent.py        # Statistical analysis agent
│   ├── synthesis_agent.py          # Decision synthesis agent
│   ├── notification_agent.py       # Email/Telegram notifications
│   ├── orchestrator.py             # Main coordinator
│   └── utils/
│       ├── __init__.py
│       ├── logging_config.py       # Logging setup
│       └── search.py               # Google Search helper
│
├── scraper/                        # Node.js scraper
│   ├── package.json                # Node.js dependencies
│   ├── src/
│   │   └── flashscore-scraper.js   # Puppeteer scraper
│   └── config/
│       └── scraper-config.js       # Scraper configuration
│
├── data/                           # Data storage
│   ├── .gitkeep
│   ├── matches.json                # Scraped matches (generated)
│   ├── results.json                # Latest results (generated)
│   └── history.json                # Historical data (generated)
│
└── logs/                           # Log files
    └── betting_system.log          # System logs (generated)
```

## File Descriptions

### Root Files

- **README.md**: Comprehensive documentation with setup, usage, and troubleshooting
- **QUICKSTART.md**: 5-minute quick start guide
- **LICENSE**: MIT License with disclaimer
- **requirements.txt**: Python package dependencies
- **setup.sh**: Automated setup script
- **run.py**: Main execution script
- **scheduler.py**: Daily scheduling system
- **.gitignore**: Excludes logs, data, credentials, node_modules

### Configuration

- **config/config.yaml**: Main configuration (sports, thresholds, notifications, scheduling)
- **config/.env.example**: Template for API keys and credentials

### Agents (Python)

#### Core Agents
- **internet_picks_agent.py**: Searches internet for betting tips and predictions
- **data_driven_agent.py**: Analyzes matches using statistics and data
- **synthesis_agent.py**: Combines analyses and makes final recommendations
- **notification_agent.py**: Sends email/Telegram notifications

#### Orchestration
- **orchestrator.py**: Coordinates all agents and workflow

#### Utilities
- **logging_config.py**: Logging setup with rotation
- **search.py**: Google Custom Search API wrapper

### Scraper (Node.js)

- **flashscore-scraper.js**: Puppeteer-based web scraper for Flashscore.com
  - Scrapes football, basketball, tennis, hockey
  - Extracts match details and bookmaker odds
  - Implements rate limiting and stealth mode

### Data Storage

- **matches.json**: Scraped match data with odds
- **results.json**: Latest betting recommendations
- **history.json**: Historical recommendations and outcomes

### Logs

- **betting_system.log**: Rotating log file with all system events

## Component Interactions

1. **Orchestrator** runs the workflow
2. **Scraper** (Node.js) fetches match data → `data/matches.json`
3. **Internet Picks Agent** analyzes each match (searches internet)
4. **Data-Driven Agent** analyzes each match (searches statistics)
5. Both agents run in **parallel** for each match
6. **Synthesis Agent** combines both analyses
7. **Synthesis Agent** makes BET/NO_BET decisions
8. Results saved to `data/results.json` and `data/history.json`
9. **Notification Agent** sends recommendations via email/Telegram
10. **Scheduler** (optional) runs daily at configured time

## Technology Stack

### Backend (Python)
- **google-genai**: Google's GenAI SDK for LLM agents
- **requests**: HTTP requests
- **beautifulsoup4**: HTML parsing
- **python-telegram-bot**: Telegram integration
- **schedule**: Cron-like scheduling
- **pyyaml**: YAML configuration
- **python-dotenv**: Environment variables

### Scraper (Node.js)
- **puppeteer**: Headless browser automation
- **puppeteer-extra**: Enhanced Puppeteer
- **puppeteer-extra-plugin-stealth**: Anti-detection
- **yaml**: Configuration parsing

### APIs
- **Google GenAI API**: LLM for analysis
- **Google Custom Search API**: Web search
- **SMTP**: Email notifications
- **Telegram Bot API**: Telegram notifications

## Data Flow

```
Flashscore.com
      ↓
[Puppeteer Scraper]
      ↓
matches.json
      ↓
[Orchestrator]
   ↙     ↘
[Internet] [Data-Driven]
 Picks      Agent
   ↓         ↓
    [Synthesis]
         ↓
    results.json
         ↓
   [Notification]
      ↙    ↘
  Email  Telegram
```

## Extensibility

### Adding New Agents
1. Create new agent in `agents/`
2. Inherit from base patterns
3. Implement `analyze_match()` method
4. Register in orchestrator

### Adding New Sports
1. Add sport to `config/config.yaml`
2. Create scraper method in `flashscore-scraper.js`
3. No agent changes needed

### Adding New Notification Channels
1. Add method in `notification_agent.py`
2. Update configuration schema
3. Add credentials to `.env.example`

## Performance Considerations

- **Parallel Processing**: Match analyses run in parallel
- **Rate Limiting**: Configurable delays in scraper
- **Caching**: 15-minute cache for Google Search results
- **Logging**: Rotating logs to prevent disk fill
- **Async I/O**: Available for future improvements

## Security

- Credentials in `.env` (git-ignored)
- API keys in environment variables
- No sensitive data in logs
- Rate limiting to prevent API abuse
- Stealth mode in scraper to avoid detection
