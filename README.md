# LinkedIn Automation Bot 🤖

AI-powered LinkedIn connection automation using Selenium with persistent Chrome profile authentication.

## 🎯 Features

- ✅ **Persistent Chrome profile** - No manual login after initial setup  
- ✅ **Works with Google OAuth** - No password needed
- ✅ **Smart action detection** - Handles Connect, Follow, Message, Pending
- ✅ **Human behavior simulation** - Random delays, natural typing patterns
- ✅ **Anti-detection measures** - Selenium hiding, realistic browsing patterns
- ✅ **Flask API** - HTTP endpoint for n8n integration
- ✅ **Comprehensive error handling** - Robust against LinkedIn UI changes

## 📋 Prerequisites

- Python 3.8+
- Google Chrome browser
- LinkedIn account
- (Optional) n8n for workflow automation

## 🚀 Quick Start

### 1. Clone & Setup

```bash
git clone https://github.com/yourusername/linkedin-bot.git
cd linkedin-bot
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. First-Time Login

```bash
python test_bot.py

# Browser will open
# Log in to LinkedIn (via Google or email)
# Session saved automatically!
```

### 3. Test It Works

```bash
# Run again - should log in automatically!
python test_bot.py
```

That's it! No configuration files needed!

## 🔧 API Server

```bash
# Start Flask API
python app.py

# Server runs on http://localhost:5000
```

## 📡 API Endpoints

### POST /send-connection

```json
{
  "linkedin_url": "https://linkedin.com/in/username",
  "connection_note": "Hi! I'd love to connect...",
  "prospect_id": "unique_id",
  "action_id": "action_id"
}
```

### GET /health

Check if bot is online and logged in.

## 🔒 Security

**Never commit these (already in `.gitignore`):**
- `chrome_bot_profile/` - Your LinkedIn session
- `.env` - Credentials (if used)
- `venv/` - Virtual environment

## 🌐 Deploy to VPS

```bash
# Option 1: Setup on VPS directly
ssh user@vps
git clone <repo>
python test_bot.py  # Use VNC to log in once

# Option 2: Transfer profile from local
scp -r chrome_bot_profile/ user@vps:/path/to/bot/
# Already logged in on VPS!
```

## ⚙️ Configuration

Optional `.env` file:

```bash
HEADLESS=false
PORT=5000
MAX_DAILY_CONNECTIONS=30
```

## 📊 Safety Limits

| Account Age | Daily Limit | Notes |
|-------------|-------------|-------|
| Week 1 | 10-15 | Start low |
| Week 2-3 | 20-30 | Normal |
| Month+ | 30-50 | Max |

## ⚠️ Disclaimer

Educational purposes only. Use responsibly and follow LinkedIn's ToS.

## 📝 License

MIT License

---

**Questions?** Open an issue on GitHub!