from flask import Flask, request, jsonify
from linkedin_bot import LinkedInBot
from config import Config
from datetime import datetime
import threading
import time

app = Flask(__name__)

# Global bot instance (stays logged in between requests)
bot = None
bot_lock = threading.Lock()

def get_bot():
    """
    Get or create bot instance
    If session is dead, automatically create a new one
    """
    global bot
    with bot_lock:
        # If bot exists, check if it's still alive
        if bot is not None:
            try:
                # Quick health check - can we access the browser?
                _ = bot.driver.current_url
                print("✅ Using existing bot session")
                return bot
            except Exception as e:
                # Session is dead - clean it up and create new one
                print(f"⚠️  Bot session died: {str(e)[:50]}")
                print("🔄 Spinning up new bot instance...")
                try:
                    bot.close()
                except:
                    pass  # Ignore errors closing dead session
                bot = None
        
        # Create fresh bot instance
        if bot is None:
            print("🤖 Creating new LinkedIn bot instance...")
            bot = LinkedInBot()
            
            print("🔐 Logging in to LinkedIn...")
            if not bot.login():
                bot = None
                raise Exception("Failed to login to LinkedIn")
            
            print("✅ Bot ready and logged in!")
        
        return bot

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'online',
        'timestamp': datetime.now().isoformat(),
        'logged_in': bot.logged_in if bot else False
    })

@app.route('/login', methods=['POST'])
def login():
    """Force login/re-login"""
    try:
        bot_instance = get_bot()
        success = bot_instance.login()
        
        return jsonify({
            'success': success,
            'message': 'Login successful' if success else 'Login failed'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/send-connection', methods=['POST'])
def send_connection():
    """
    Send LinkedIn connection request
    
    Expected JSON body:
    {
        "linkedin_url": "https://linkedin.com/in/username",
        "connection_note": "Hi! I'd love to connect...",
        "prospect_id": "patrick_stripe_001",
        "action_id": "patrick_stripe_001_linkedin_001"
    }
    """
    try:
        data = request.json
        
        # Validate required fields
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        linkedin_url = data.get('linkedin_url')
        connection_note = data.get('connection_note', '')
        prospect_id = data.get('prospect_id')
        action_id = data.get('action_id')
        
        if not linkedin_url:
            return jsonify({
                'success': False,
                'error': 'linkedin_url is required'
            }), 400
        
        if not prospect_id:
            return jsonify({
                'success': False,
                'error': 'prospect_id is required'
            }), 400
        
        print(f"\n{'='*60}")
        print(f"📨 NEW CONNECTION REQUEST")
        print(f"{'='*60}")
        print(f"Prospect ID: {prospect_id}")
        print(f"Action ID: {action_id}")
        print(f"Profile URL: {linkedin_url}")
        print(f"Message Length: {len(connection_note)} chars")
        print(f"{'='*60}\n")
        
        # Get bot instance (creates new one if session died)
        bot_instance = get_bot()
        
        # Send connection request
        result = bot_instance.send_connection_request(linkedin_url, connection_note)
        
        # Add tracking info to result
        result['prospect_id'] = prospect_id
        result['action_id'] = action_id
        result['timestamp'] = datetime.now().isoformat()
        
        if result['success']:
            print(f"\n✅ SUCCESS: Connection request sent to {prospect_id}\n")
            return jsonify(result), 200
        else:
            print(f"\n❌ FAILED: {result.get('error')}\n")
            return jsonify(result), 500
            
    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ ERROR: {error_msg}\n")
        
        # If ANY error occurs, mark bot as needing recreation
        # Next request will get a fresh bot instance
        global bot
        if 'session' in error_msg.lower() or 'chrome' in error_msg.lower() or 'driver' in error_msg.lower():
            print("🔄 Marking bot for recreation on next request...")
            with bot_lock:
                try:
                    if bot:
                        bot.close()
                except:
                    pass
                bot = None
        
        return jsonify({
            'success': False,
            'error': error_msg,
            'prospect_id': data.get('prospect_id') if data else None,
            'action_id': data.get('action_id') if data else None,
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/close', methods=['POST'])
def close_bot():
    """Close the bot and browser"""
    global bot
    try:
        if bot:
            bot.close()
            bot = None
        return jsonify({
            'success': True,
            'message': 'Bot closed'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Validate configuration
    try:
        Config.validate()
        print("\n" + "="*60)
        print("🚀 LINKEDIN BOT API SERVER")
        print("="*60)
        print(f"Email: {Config.LINKEDIN_EMAIL}")
        print(f"Headless: {Config.HEADLESS}")
        print(f"Port: {Config.PORT}")
        print(f"Max Daily Connections: {Config.MAX_DAILY_CONNECTIONS}")
        print("="*60 + "\n")
        
        # Start Flask server
        app.run(
            host='0.0.0.0',
            port=Config.PORT,
            debug=False  # Set to False in production
        )
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("Please check your .env file\n")