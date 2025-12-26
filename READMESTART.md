# LinkedIn Bot - Automated Connection Requests

Selenium-based LinkedIn automation for sending personalized connection requests.

## Features

- ✅ Automated connection requests with personalized notes
- ✅ Human behavior simulation (random delays, typing speed)
- ✅ Anti-detection measures
- ✅ Flask API for n8n integration
- ✅ Runs locally or on VPS
- ✅ Session persistence (stays logged in)

## Prerequisites

- Python 3.8 or higher
- Google Chrome browser
- LinkedIn account

## Local Setup (30 minutes)

### 1. Install Python Dependencies

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your LinkedIn credentials
nano .env
```

Required in `.env`:
```
LINKEDIN_EMAIL=your-email@domain.com
LINKEDIN_PASSWORD=your-password
HEADLESS=false
PORT=5000
```

### 3. Test the Bot

```bash
# Run local tests
python test_bot.py
```

This will:
1. Test LinkedIn login
2. (Optional) Send a test connection request

**Watch Chrome open and perform actions!**

### 4. Start the API Server

```bash
# Start Flask server
python app.py
```

Server runs on: `http://localhost:5000`

### 5. Test API Endpoints

```bash
# Health check
curl http://localhost:5000/health

# Send connection request
curl -X POST http://localhost:5000/send-connection \
  -H "Content-Type: application/json" \
  -d '{
    "linkedin_url": "https://linkedin.com/in/test",
    "connection_note": "Hi! I would love to connect...",
    "prospect_id": "test_001",
    "action_id": "test_001_linkedin_001"
  }'
```

## API Endpoints

### GET /health
Health check endpoint

**Response:**
```json
{
  "status": "online",
  "timestamp": "2025-12-23T10:00:00Z",
  "logged_in": true
}
```

### POST /send-connection
Send LinkedIn connection request

**Request Body:**
```json
{
  "linkedin_url": "https://linkedin.com/in/username",
  "connection_note": "Personalized message (max 300 chars)",
  "prospect_id": "unique_prospect_id",
  "action_id": "unique_action_id"
}
```

**Success Response:**
```json
{
  "success": true,
  "profile_url": "https://linkedin.com/in/username",
  "message_sent": true,
  "prospect_id": "unique_prospect_id",
  "action_id": "unique_action_id",
  "timestamp": "2025-12-23T10:00:00Z"
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Error message",
  "prospect_id": "unique_prospect_id",
  "timestamp": "2025-12-23T10:00:00Z"
}
```

## Integration with n8n

### 1. Make Local Server Accessible

**Option A: Use ngrok (For Testing)**
```bash
# Install ngrok: https://ngrok.com/
ngrok http 5000

# Use the https URL in n8n (e.g., https://abc123.ngrok.io)
```

**Option B: Deploy to VPS (For Production)**
- See VPS_DEPLOYMENT.md for instructions

### 2. Create n8n Workflow

Add HTTP Request node:
- **Method:** POST
- **URL:** `http://localhost:5000/send-connection` (or ngrok URL)
- **Body:** JSON
```json
{
  "linkedin_url": "{{ $json.linkedin_url }}",
  "connection_note": "{{ $json.connection_note }}",
  "prospect_id": "{{ $json.prospect_id }}",
  "action_id": "{{ $json.action_id }}"
}
```

## Safety Features

### Built-in Protections
- Random delays (2-5 seconds between actions)
- Human-like typing speed (50-200ms per character)
- Random mouse movements
- Session persistence (no repeated logins)
- Daily connection limits (configurable)

### Recommended Daily Limits
- **Conservative:** 10-15 connections/day
- **Moderate:** 20-30 connections/day
- **Aggressive:** 40-50 connections/day (higher risk)

## Troubleshooting

### "Login failed"
- Check credentials in .env
- LinkedIn may require verification code
- Try running with HEADLESS=false to see what's happening

### "Connect button not found"
- May already be connected to this person
- Connection request may be pending
- Profile may not allow connections

### Chrome/ChromeDriver errors
```bash
# Update ChromeDriver
pip install --upgrade webdriver-manager
```

## Project Structure

```
linkedin-bot/
├── app.py                  # Flask API server
├── linkedin_bot.py         # Main bot logic
├── anti_detection.py       # Human behavior simulation
├── config.py              # Configuration management
├── test_bot.py            # Local testing script
├── requirements.txt       # Python dependencies
├── .env                   # Your credentials (DO NOT COMMIT)
└── README.md              # This file
```

## Security Notes

- ⚠️ Never commit .env file to git
- ⚠️ Use app passwords if available
- ⚠️ Start with low daily limits
- ⚠️ Monitor for LinkedIn warning emails
- ⚠️ Use residential proxy for production

## Next Steps

1. ✅ Test locally with test_bot.py
2. ✅ Build n8n workflow
3. ✅ Test end-to-end with 1-2 real connections
4. ✅ Monitor acceptance rates
5. ✅ Deploy to VPS for 24/7 operation

## Support

Issues? Check:
1. .env file is configured correctly
2. Chrome is installed
3. Virtual environment is activated
4. All dependencies are installed
