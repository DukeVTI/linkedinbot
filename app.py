from flask import Flask, request, jsonify
from linkedin_bot import LinkedInBot
from config import Config
from datetime import datetime
import threading
import time
import random

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

@app.route('/visit-profile', methods=['POST'])
def visit_profile():
    """
    Visit a LinkedIn profile without taking action (Warmup Day 1-2)
    
    Expected JSON body:
    {
        "linkedin_url": "https://linkedin.com/in/username",
        "prospect_id": "patrick_stripe_001"
    }
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        linkedin_url = data.get('linkedin_url')
        prospect_id = data.get('prospect_id', 'unknown')
        
        if not linkedin_url:
            return jsonify({
                'success': False,
                'error': 'linkedin_url is required'
            }), 400
        
        print(f"\n{'='*60}")
        print(f"👀 PROFILE VISIT (WARMUP)")
        print(f"{'='*60}")
        print(f"Prospect ID: {prospect_id}")
        print(f"Profile URL: {linkedin_url}")
        print(f"{'='*60}\n")
        
        # Get bot instance
        bot_instance = get_bot()
        
        # Navigate to profile
        print(f"🌐 Navigating to profile...")
        bot_instance.driver.get(linkedin_url)
        from anti_detection import human_delay, scroll_slowly
        human_delay(5, 8)
        
        # Scroll down slowly (reading profile)
        print("📜 Scrolling through profile...")
        scroll_slowly(bot_instance.driver, 300)
        human_delay(3, 5)
        
        # Scroll again
        scroll_slowly(bot_instance.driver, 300)
        human_delay(3, 5)
        
        # Stay for 10-20 seconds (human reading)
        print("📖 Reading profile content...")
        human_delay(10, 20)
        
        print("✅ Profile visit completed!")
        
        return jsonify({
            'success': True,
            'action_taken': 'profile_visit',
            'profile_url': linkedin_url,
            'prospect_id': prospect_id,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ ERROR: {error_msg}\n")
        
        return jsonify({
            'success': False,
            'error': error_msg,
            'prospect_id': data.get('prospect_id') if data else None,
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/react-to-post', methods=['POST'])
def react_to_post():
    """
    Like or react to a LinkedIn post (Warmup Day 3-4)
    
    Expected JSON body:
    {
        "linkedin_url": "https://linkedin.com/in/username",
        "prospect_id": "patrick_stripe_001",
        "reaction_type": "like"
    }
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        linkedin_url = data.get('linkedin_url')
        prospect_id = data.get('prospect_id', 'unknown')
        reaction_type = data.get('reaction_type', 'like')
        
        if not linkedin_url:
            return jsonify({
                'success': False,
                'error': 'linkedin_url is required'
            }), 400
        
        print(f"\n{'='*60}")
        print(f"❤️ POST REACTION (WARMUP) - {reaction_type.upper()}")
        print(f"{'='*60}")
        print(f"Prospect ID: {prospect_id}")
        print(f"Profile URL: {linkedin_url}")
        print(f"{'='*60}\n")
        
        # Get bot instance
        bot_instance = get_bot()
        
        # Navigate to profile
        print(f"🌐 Navigating to profile...")
        bot_instance.driver.get(linkedin_url)
        from anti_detection import human_delay, scroll_slowly
        from selenium.webdriver.common.by import By
        human_delay(5, 8)
        
        # Scroll to find posts
        print("📜 Looking for posts...")
        scroll_slowly(bot_instance.driver, 500)
        human_delay(3, 5)
        
        # Find reaction buttons
        reaction_success = False
        try:
            # Look for Like/React buttons
            like_buttons = bot_instance.driver.find_elements(By.XPATH, 
                "//button[contains(@aria-label, 'React') or contains(@aria-label, 'Like')]")
            
            if like_buttons and len(like_buttons) > 0:
                print(f"  ✅ Found {len(like_buttons)} posts with reaction buttons")
                
                # Click the first one
                first_button = like_buttons[0]
                first_button.click()
                human_delay(2, 4)
                
                print(f"  ✅ Reacted to post!")
                reaction_success = True
            else:
                print("  ⚠️ No posts found with reaction buttons")
                
        except Exception as e:
            print(f"  ⚠️ Could not react to post: {str(e)[:100]}")
        
        return jsonify({
            'success': True,
            'action_taken': 'post_reaction',
            'reaction_type': reaction_type,
            'reaction_success': reaction_success,
            'profile_url': linkedin_url,
            'prospect_id': prospect_id,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ ERROR: {error_msg}\n")
        
        return jsonify({
            'success': False,
            'error': error_msg,
            'prospect_id': data.get('prospect_id') if data else None,
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/comment-on-post', methods=['POST'])
def comment_on_post():
    """
    Comment on a LinkedIn post (Warmup Day 5-6)
    
    Expected JSON body:
    {
        "linkedin_url": "https://linkedin.com/in/username",
        "prospect_id": "patrick_stripe_001",
        "comment_text": "Great insights! This really resonates..."
    }
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        linkedin_url = data.get('linkedin_url')
        prospect_id = data.get('prospect_id', 'unknown')
        comment_text = data.get('comment_text', '')
        
        if not linkedin_url:
            return jsonify({
                'success': False,
                'error': 'linkedin_url is required'
            }), 400
        
        if not comment_text:
            return jsonify({
                'success': False,
                'error': 'comment_text is required'
            }), 400
        
        print(f"\n{'='*60}")
        print(f"💬 POST COMMENT (WARMUP)")
        print(f"{'='*60}")
        print(f"Prospect ID: {prospect_id}")
        print(f"Profile URL: {linkedin_url}")
        print(f"Comment: {comment_text[:50]}...")
        print(f"{'='*60}\n")
        
        # Get bot instance
        bot_instance = get_bot()
        
        # Navigate to profile
        print(f"🌐 Navigating to profile...")
        bot_instance.driver.get(linkedin_url)
        from anti_detection import human_delay, scroll_slowly, human_type
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.common.action_chains import ActionChains
        from selenium.webdriver.common.keys import Keys
        
        human_delay(5, 8)
        
        # Scroll to find posts
        print("📜 Looking for posts...")
        scroll_slowly(bot_instance.driver, 500)
        human_delay(3, 5)
        
        # Find and comment on first post
        comment_success = False
        try:
            # Find comment buttons
            comment_buttons = bot_instance.driver.find_elements(By.XPATH, 
                "//button[contains(@aria-label, 'Comment') or contains(@class, 'comment-button')]")
            
            if comment_buttons and len(comment_buttons) > 0:
                print(f"  ✅ Found {len(comment_buttons)} posts with comment buttons")
                
                # Click first comment button to open comment box
                first_button = comment_buttons[0]
                
                # Try multiple click strategies
                clicked = False
                try:
                    first_button.click()
                    clicked = True
                    print(f"  ✅ Clicked comment button (normal click)")
                except:
                    try:
                        bot_instance.driver.execute_script("arguments[0].click();", first_button)
                        clicked = True
                        print(f"  ✅ Clicked comment button (JavaScript)")
                    except:
                        print(f"  ❌ Could not click comment button")
                
                if clicked:
                    human_delay(2, 3)
                    
                    # Find comment text area - try multiple selectors
                    comment_box = None
                    selectors = [
                        "//div[@role='textbox' and @contenteditable='true']",
                        "//div[contains(@class, 'ql-editor')]",
                        "//div[@data-placeholder='Add a comment…']",
                        "//div[contains(@class, 'comments-comment-box__form')]//div[@contenteditable='true']"
                    ]
                    
                    for selector in selectors:
                        try:
                            boxes = bot_instance.driver.find_elements(By.XPATH, selector)
                            # Get the last one (most recent, just opened)
                            if boxes and len(boxes) > 0:
                                comment_box = boxes[-1]
                                print(f"  ✅ Found comment box (selector: {selector[:50]}...)")
                                break
                        except:
                            continue
                    
                    if comment_box:
                        # Click to focus
                        print(f"  🎯 Clicking comment box to focus...")
                        try:
                            comment_box.click()
                            human_delay(1, 2)
                            print(f"  ✅ Focused on comment box")
                        except Exception as e:
                            print(f"  ⚠️ Click failed: {str(e)[:30]}")
                        
                        # Type comment - try multiple methods for contenteditable divs
                        print(f"  ⌨️ Typing comment...")
                        typing_success = False
                        
                        # Method 1: JavaScript innerHTML (best for contenteditable)
                        try:
                            print(f"  📝 Method 1: JavaScript innerHTML...")
                            # Use JavaScript to set the text
                            script = f"arguments[0].innerHTML = '{comment_text}';"
                            bot_instance.driver.execute_script(script, comment_box)
                            human_delay(1, 2)
                            
                            # Trigger input event so LinkedIn knows text changed
                            bot_instance.driver.execute_script(
                                "arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", 
                                comment_box
                            )
                            human_delay(1, 2)
                            
                            # Verify text is there
                            current_content = bot_instance.driver.execute_script("return arguments[0].innerHTML;", comment_box)
                            if current_content and comment_text in current_content:
                                print(f"  ✅ Comment typed successfully (JavaScript)")
                                print(f"  📝 Content: {current_content[:50]}...")
                                typing_success = True
                            else:
                                print(f"  ⚠️ JavaScript set but content not verified")
                        except Exception as e:
                            print(f"  ⚠️ Method 1 failed: {str(e)[:50]}")
                        
                        # Method 2: send_keys (backup)
                        if not typing_success:
                            try:
                                print(f"  📝 Method 2: send_keys...")
                                comment_box.send_keys(comment_text)
                                human_delay(2, 3)
                                
                                # Check with JavaScript
                                current_content = bot_instance.driver.execute_script("return arguments[0].innerHTML || arguments[0].textContent;", comment_box)
                                if current_content and len(current_content.strip()) > 0:
                                    print(f"  ✅ Comment typed (send_keys)")
                                    print(f"  📝 Content: {current_content[:50]}...")
                                    typing_success = True
                                else:
                                    print(f"  ⚠️ send_keys executed but no content")
                            except Exception as e:
                                print(f"  ⚠️ Method 2 failed: {str(e)[:50]}")
                        
                        # Method 3: ActionChains (for stubborn elements)
                        if not typing_success:
                            try:
                                print(f"  📝 Method 3: ActionChains...")
                                actions = ActionChains(bot_instance.driver)
                                actions.move_to_element(comment_box).click().send_keys(comment_text).perform()
                                human_delay(2, 3)
                                
                                # Check with JavaScript
                                current_content = bot_instance.driver.execute_script("return arguments[0].innerHTML || arguments[0].textContent;", comment_box)
                                if current_content and len(current_content.strip()) > 0:
                                    print(f"  ✅ Comment typed (ActionChains)")
                                    print(f"  📝 Content: {current_content[:50]}...")
                                    typing_success = True
                                else:
                                    print(f"  ⚠️ ActionChains executed but no content")
                            except Exception as e:
                                print(f"  ⚠️ Method 3 failed: {str(e)[:50]}")
                        
                        # Method 4: human_type with character-by-character (last resort)
                        if not typing_success:
                            try:
                                print(f"  📝 Method 4: human_type character-by-character...")
                                # Clear first
                                comment_box.clear()
                                human_delay(0.5, 1)
                                
                                # Type slowly
                                for char in comment_text:
                                    comment_box.send_keys(char)
                                    time.sleep(random.uniform(0.05, 0.15))
                                
                                human_delay(1, 2)
                                
                                # Check with JavaScript
                                current_content = bot_instance.driver.execute_script("return arguments[0].innerHTML || arguments[0].textContent;", comment_box)
                                if current_content and len(current_content.strip()) > 0:
                                    print(f"  ✅ Comment typed (character-by-character)")
                                    print(f"  📝 Content: {current_content[:50]}...")
                                    typing_success = True
                                else:
                                    print(f"  ⚠️ Typed but no content detected")
                            except Exception as e:
                                print(f"  ⚠️ Method 4 failed: {str(e)[:50]}")
                        
                        # If typing failed completely, abort
                        if not typing_success:
                            print(f"  ❌ ALL TYPING METHODS FAILED")
                            print(f"  💡 Cannot post empty comment")
                            raise Exception("Failed to type comment - all methods exhausted")
                        
                        # Now submit the comment - Ember.js-aware submission
                        print(f"  📤 Submitting comment (Ember.js method)...")
                        submit_success = False
                        
                        # First, scroll the comment box into view
                        try:
                            bot_instance.driver.execute_script(
                                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", 
                                comment_box
                            )
                            human_delay(1, 2)
                            print(f"  ✅ Scrolled comment box into view")
                        except Exception as e:
                            print(f"  ⚠️ Scroll failed: {str(e)[:30]}")
                        
                        # Method 1: Find and trigger Ember component click
                        try:
                            print(f"  📝 Method 1: Ember-aware click...")
                            
                            # Find button using the specific class we saw in inspector
                            buttons = bot_instance.driver.find_elements(By.XPATH, 
                                "//button[contains(@class, 'comments-comment-box__submit-button')]")
                            
                            if buttons:
                                submit_button = buttons[-1]  # Last one (most recent)
                                
                                # Scroll into view
                                bot_instance.driver.execute_script(
                                    "arguments[0].scrollIntoView({block: 'nearest'});", 
                                    submit_button
                                )
                                human_delay(0.5, 1)
                                
                                # Trigger comprehensive click events that Ember listens for
                                bot_instance.driver.execute_script("""
                                    var button = arguments[0];
                                    
                                    // Make sure button is enabled
                                    button.disabled = false;
                                    button.removeAttribute('disabled');
                                    
                                    // Focus the button first
                                    button.focus();
                                    
                                    // Create and dispatch all mouse events that Ember might listen for
                                    var events = ['mouseenter', 'mouseover', 'mousedown', 'focus', 'mouseup', 'click'];
                                    
                                    events.forEach(function(eventType) {
                                        var event = new MouseEvent(eventType, {
                                            view: window,
                                            bubbles: true,
                                            cancelable: true,
                                            buttons: 1
                                        });
                                        button.dispatchEvent(event);
                                    });
                                    
                                    // Also trigger pointer events (modern browsers)
                                    var pointerEvents = ['pointerdown', 'pointerup'];
                                    pointerEvents.forEach(function(eventType) {
                                        var event = new PointerEvent(eventType, {
                                            view: window,
                                            bubbles: true,
                                            cancelable: true,
                                            isPrimary: true
                                        });
                                        button.dispatchEvent(event);
                                    });
                                """, submit_button)
                                
                                human_delay(2, 3)
                                print(f"  ✅ Triggered Ember events")
                                submit_success = True
                            else:
                                print(f"  ⚠️ Submit button not found")
                        except Exception as e:
                            print(f"  ⚠️ Method 1 failed: {str(e)[:50]}")
                        
                        # Method 2: Find the Ember component and trigger its action directly
                        if not submit_success:
                            try:
                                print(f"  📝 Method 2: Direct Ember action trigger...")
                                
                                bot_instance.driver.execute_script("""
                                    // Find the comment box's parent form
                                    var commentBox = arguments[0];
                                    var form = commentBox.closest('form');
                                    
                                    if (form) {
                                        // Find the submit button within this form
                                        var submitButton = form.querySelector('button[type="submit"], button[class*="submit-button"]');
                                        
                                        if (submitButton) {
                                            // Click it multiple ways
                                            submitButton.click();
                                            
                                            // Try to find and trigger Ember view's click handler
                                            if (submitButton.__ember_meta__) {
                                                // This is an Ember component
                                                var emberClick = new Event('click', {bubbles: true, cancelable: true});
                                                submitButton.dispatchEvent(emberClick);
                                            }
                                            
                                            // Also submit the form
                                            if (form.onsubmit) {
                                                form.onsubmit();
                                            }
                                            form.submit();
                                        }
                                    }
                                """, comment_box)
                                
                                human_delay(2, 3)
                                print(f"  ✅ Triggered Ember component")
                                submit_success = True
                            except Exception as e:
                                print(f"  ⚠️ Method 2 failed: {str(e)[:50]}")
                        
                        # Method 3: Selenium ActionChains with real mouse movement
                        if not submit_success:
                            try:
                                print(f"  📝 Method 3: Real mouse movement...")
                                
                                buttons = bot_instance.driver.find_elements(By.XPATH, 
                                    "//button[contains(@class, 'comments-comment-box__submit-button')]")
                                
                                if buttons:
                                    submit_button = buttons[-1]
                                    
                                    # Scroll into view
                                    bot_instance.driver.execute_script(
                                        "arguments[0].scrollIntoView({block: 'center'});", 
                                        submit_button
                                    )
                                    human_delay(1, 2)
                                    
                                    # Use ActionChains for human-like interaction
                                    actions = ActionChains(bot_instance.driver)
                                    
                                    # Move to button
                                    actions.move_to_element(submit_button)
                                    actions.pause(0.5)
                                    
                                    # Click and hold briefly (more human-like)
                                    actions.click_and_hold()
                                    actions.pause(0.1)
                                    actions.release()
                                    
                                    # Execute the chain
                                    actions.perform()
                                    
                                    human_delay(2, 3)
                                    print(f"  ✅ Clicked with ActionChains")
                                    submit_success = True
                            except Exception as e:
                                print(f"  ⚠️ Method 3 failed: {str(e)[:50]}")
                        
                        # Method 4: Tab to button and press Space/Enter
                        if not submit_success:
                            try:
                                print(f"  📝 Method 4: Keyboard navigation...")
                                
                                # Press Tab to move focus from comment box to button
                                comment_box.send_keys(Keys.TAB)
                                human_delay(0.5, 1)
                                
                                # Get the currently focused element
                                focused = bot_instance.driver.switch_to.active_element
                                
                                # Press Space (activates buttons in HTML)
                                focused.send_keys(Keys.SPACE)
                                human_delay(1, 2)
                                
                                print(f"  ✅ Pressed Tab + Space")
                                submit_success = True
                            except Exception as e:
                                print(f"  ⚠️ Method 4 failed: {str(e)[:50]}")
                        
                        # Method 5: Enter key (last resort)
                        if not submit_success:
                            try:
                                print(f"  📝 Method 5: Enter key...")
                                comment_box.send_keys(Keys.RETURN)
                                human_delay(2, 3)
                                print(f"  ✅ Pressed Enter")
                                submit_success = True
                            except Exception as e:
                                print(f"  ⚠️ Method 5 failed: {str(e)[:50]}")
                        
                        if submit_success:
                            human_delay(3, 5)
                                
                        if submit_success:
                            human_delay(3, 5)
                            
                            # Verify comment was posted
                            print(f"  🔍 Verifying comment was posted...")
                            try:
                                # Check if text was cleared from comment box
                                try:
                                    current_content = bot_instance.driver.execute_script(
                                        "return arguments[0].innerHTML || arguments[0].textContent || '';", 
                                        comment_box
                                    )
                                    current_text = current_content.strip()
                                    
                                    if len(current_text) == 0:
                                        print(f"  ✅ VERIFIED: Comment box is now empty!")
                                        comment_success = True
                                    elif comment_text.strip() not in current_text:
                                        print(f"  ✅ VERIFIED: Our comment text is gone!")
                                        comment_success = True
                                    else:
                                        print(f"  ⚠️ Text still in box after Enter")
                                        print(f"  📝 Box content: '{current_text[:50]}...'")
                                        # Could still be a timing issue - wait a bit more
                                        human_delay(2, 3)
                                        # Check again
                                        current_content = bot_instance.driver.execute_script(
                                            "return arguments[0].innerHTML || arguments[0].textContent || '';", 
                                            comment_box
                                        )
                                        current_text = current_content.strip()
                                        if len(current_text) == 0 or comment_text.strip() not in current_text:
                                            print(f"  ✅ VERIFIED: Comment cleared (slight delay)")
                                            comment_success = True
                                        else:
                                            print(f"  ❌ FAILED: Text still there after retry")
                                            comment_success = False
                                except:
                                    # If we can't access the box, it probably closed (success)
                                    print(f"  ✅ VERIFIED: Comment box no longer accessible (posted!)")
                                    comment_success = True
                                    
                            except Exception as e:
                                print(f"  ⚠️ Could not verify: {str(e)[:50]}")
                                # If we can't verify, be conservative and assume failure
                                comment_success = False
                            
                            if comment_success:
                                print(f"  🎉 COMMENT POSTED SUCCESSFULLY!")
                            else:
                                print(f"  ❌ COMMENT FAILED TO POST!")
                        else:
                            print(f"  ❌ Failed to submit comment (Enter key didn't work)")
                    else:
                        print(f"  ❌ Could not find comment text box")
            else:
                print("  ⚠️ No posts found with comment buttons")
                
        except Exception as e:
            print(f"  ❌ Error in comment flow: {str(e)[:100]}")
            import traceback
            traceback.print_exc()
        
        return jsonify({
            'success': comment_success,
            'action_taken': 'post_comment',
            'comment_success': comment_success,
            'comment_text': comment_text if comment_success else '',
            'profile_url': linkedin_url,
            'prospect_id': prospect_id,
            'timestamp': datetime.now().isoformat()
        }), 200 if comment_success else 500
        
    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ ERROR: {error_msg}\n")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': error_msg,
            'prospect_id': data.get('prospect_id') if data else None,
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