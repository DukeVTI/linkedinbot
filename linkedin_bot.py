from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time
import json
import os
import platform
from config import Config
from anti_detection import human_delay, human_type, scroll_slowly

class LinkedInBot:
    """LinkedIn automation bot using Selenium with cookie-based authentication"""
    
    def __init__(self):
        """Initialize the bot with Chrome WebDriver"""
        self.driver = None
        self.logged_in = False
        self.cookies_file = 'linkedin_cookies.json'
        self._init_driver()
        
    def _init_driver(self):
        """Initialize Chrome WebDriver with anti-detection settings"""
        print("🚀 Initializing Chrome WebDriver...")
        
        # Import platform at function level
        import platform
        
        options = webdriver.ChromeOptions()
        
        # USE PERSISTENT PROFILE (not temporary)
        # This ensures cookies persist between sessions
        if not Config.HEADLESS:
            # Create a persistent profile directory for the bot
            bot_profile_dir = os.path.join(os.getcwd(), 'chrome_bot_profile')
            
            # Create directory if it doesn't exist
            if not os.path.exists(bot_profile_dir):
                os.makedirs(bot_profile_dir)
                print(f"📁 Created persistent Chrome profile: {bot_profile_dir}")
            else:
                print(f"📂 Using persistent Chrome profile: {bot_profile_dir}")
            
            # Use this persistent profile
            options.add_argument(f"user-data-dir={bot_profile_dir}")
            
            print("✅ Cookies will persist between sessions!")
        else:
            print("📂 Using temporary Chrome profile (headless mode)")
        
        # Headless mode (no visible browser window)
        if Config.HEADLESS:
            options.add_argument('--headless')
            print("👻 Running in headless mode (no browser window)")
        else:
            print("👀 Running with visible browser window")
        
        # Anti-detection settings
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Fix for DevToolsActivePort error (Windows)
        options.add_argument('--remote-debugging-port=9222')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        
        # Increase page load timeout settings
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-infobars')
        
        # Set realistic window size
        options.add_argument('--window-size=1920,1080')
        
        # Disable logging spam
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        # Use webdriver-manager to auto-download correct ChromeDriver
        service = Service(ChromeDriverManager().install())
        
        # Suppress ChromeDriver logs
        service.log_path = 'NUL' if platform.system() == 'Windows' else '/dev/null'
        
        self.driver = webdriver.Chrome(service=service, options=options)
        
        # Set page load timeout to 60 seconds (instead of default 300)
        self.driver.set_page_load_timeout(60)
        
        # Implicit wait for elements
        self.driver.implicitly_wait(10)
        
        # Execute CDP commands to hide webdriver property
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })
        
        print("✅ Chrome WebDriver initialized successfully")
    
    def save_cookies(self):
        """
        Save current session cookies to file
        Call this after logging in manually via Google
        """
        print(f"💾 Saving cookies to {self.cookies_file}...")
        
        cookies = self.driver.get_cookies()
        
        with open(self.cookies_file, 'w') as f:
            json.dump(cookies, f, indent=2)
        
        print(f"✅ Saved {len(cookies)} cookies")
        print(f"✅ Cookies saved to {self.cookies_file}")
        
        return True
    
    def load_cookies(self):
        """
        Load cookies from file and apply to browser
        This logs us in without needing password
        """
        if not os.path.exists(self.cookies_file):
            print(f"❌ Cookie file not found: {self.cookies_file}")
            print("👉 Run manual_login_and_save_cookies() first")
            return False
        
        print(f"🔄 Loading cookies from {self.cookies_file}...")
        
        # Must visit LinkedIn first before adding cookies
        self.driver.get('https://www.linkedin.com')
        human_delay(2, 3)
        
        # Load cookies from file
        with open(self.cookies_file, 'r') as f:
            cookies = json.load(f)
        
        print(f"📥 Found {len(cookies)} cookies to load")
        
        # Add each cookie to browser
        loaded_count = 0
        for cookie in cookies:
            try:
                # Remove keys that might cause issues
                if 'sameSite' in cookie and cookie['sameSite'] not in ['Strict', 'Lax', 'None']:
                    cookie['sameSite'] = 'None'
                if 'expiry' in cookie:
                    cookie['expiry'] = int(cookie['expiry'])
                    
                self.driver.add_cookie(cookie)
                loaded_count += 1
            except Exception as e:
                # Skip cookies that can't be added (expired, etc.)
                continue
        
        print(f"✅ Loaded {loaded_count}/{len(cookies)} cookies")
        
        # Refresh page to apply cookies with timeout handling
        print("🔄 Refreshing page to apply cookies...")
        try:
            # Use JavaScript to refresh instead of driver.refresh() to avoid timeout
            self.driver.execute_script("window.location.reload();")
            human_delay(3, 5)
        except Exception as e:
            print(f"  ⚠️  Refresh warning: {str(e)[:100]}")
            # Continue anyway - cookies might still work
        
        return True
    
    def check_login_status(self):
        """Check if we're currently logged in"""
        try:
            current_url = self.driver.current_url
            
            # Check if we're on a logged-in page
            if any(path in current_url for path in ['feed', 'mynetwork', 'messaging', 'notifications', 'jobs']):
                print("✅ Successfully logged in!")
                self.logged_in = True
                return True
            
            # Also check for LinkedIn navigation elements (indicates logged in)
            try:
                # Look for the "Me" dropdown which only appears when logged in
                me_button = self.driver.find_element(By.XPATH, "//button[contains(@class, 'global-nav__primary-link--me')]")
                if me_button:
                    print("✅ Successfully logged in!")
                    self.logged_in = True
                    return True
            except:
                pass
            
            # If we're on linkedin.com root or /in/*, we might be logged in
            if 'linkedin.com' in current_url and '/uas/login' not in current_url:
                print("⚠️  Appears to be logged in (on LinkedIn domain)")
                self.logged_in = True
                return True
            
            print(f"⚠️  Not logged in. Current URL: {current_url}")
            self.logged_in = False
            return False
            
        except Exception as e:
            print(f"⚠️  Could not verify login status: {str(e)[:100]}")
            self.logged_in = False
            return False
    
    def manual_login_and_save_cookies(self):
        """
        ONE-TIME SETUP: Manual login, Chrome profile saves everything automatically
        
        You just need to log in once. After that, the Chrome profile
        remembers your session permanently - no cookie files needed!
        """
        print("\n" + "="*60)
        print("🔐 MANUAL LOGIN - ONE-TIME SETUP")
        print("="*60)
        print("\nLog in to LinkedIn once, and Chrome will remember your session.")
        print("No need to log in again (until session expires in ~90 days).")
        print("\n" + "="*60 + "\n")
        
        print("📂 Opening LinkedIn...")
        self.driver.get('https://www.linkedin.com/login')
        human_delay(3, 5)
        
        print("\n" + "="*60)
        print("👉 PLEASE LOG IN TO LINKEDIN NOW")
        print("="*60)
        print("\nOptions:")
        print("  1. Click 'Sign in with Google' (recommended)")
        print("  2. Or use email + password if you have one")
        print("\nAfter logging in, you should see your LinkedIn feed.")
        print("\n" + "="*60 + "\n")
        
        input("Press ENTER after you've logged in successfully...")
        
        # Check if login was successful
        if not self.check_login_status():
            print("\n❌ Login verification failed!")
            print("Please make sure you're logged in and try again.")
            return False
        
        print("\n" + "="*60)
        print("✅ LOGIN COMPLETE!")
        print("="*60)
        print("\nYour session is now saved in the Chrome profile.")
        print("Chrome will automatically remember you next time - no manual")
        print("login needed until the session expires (~90 days).")
        print("\n" + "="*60 + "\n")
        
        return True
        
    def login(self):
        """
        Log into LinkedIn using persistent Chrome profile
        
        With persistent profile, Chrome automatically loads all session data
        (cookies, local storage, etc.) so manual login is usually not needed!
        """
        if self.logged_in:
            print("✅ Already logged in")
            return True
        
        print("🔐 Checking login status...")
        
        # Navigate to LinkedIn
        self.driver.get('https://www.linkedin.com/feed')
        human_delay(3, 5)
        
        # Check if we're logged in (Chrome should have loaded session from profile)
        if self.check_login_status():
            print("✅ Logged in automatically via persistent Chrome profile!")
            return True
        
        # If not logged in, user needs to log in manually and we'll save the session
        print("❌ Not logged in - persistent profile doesn't have valid session")
        print("👉 Run: bot.manual_login_and_save_cookies()")
        print("👉 Or just browse to linkedin.com and log in manually in this browser")
        return False
    
    def login_with_password(self):
        """
        LEGACY: Log into LinkedIn with email + password
        Only works if you have a password-enabled account
        """
        if self.logged_in:
            print("✅ Already logged in")
            return True
            
        print("🔐 Logging into LinkedIn...")
        
        try:
            # Navigate to LinkedIn login page
            self.driver.get('https://www.linkedin.com/login')
            human_delay(3, 5)
            
            # Find and fill email field
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'username'))
            )
            human_type(email_field, Config.LINKEDIN_EMAIL)
            human_delay(1, 2)
            
            # Find and fill password field
            password_field = self.driver.find_element(By.ID, 'password')
            human_type(password_field, Config.LINKEDIN_PASSWORD, min_delay=0.08, max_delay=0.15)
            human_delay(1, 2)
            
            # Click sign in button
            sign_in_button = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            sign_in_button.click()
            
            print("⏳ Waiting for login to complete...")
            human_delay(5, 8)
            
            # Check if login was successful
            if 'feed' in self.driver.current_url or 'mynetwork' in self.driver.current_url:
                self.logged_in = True
                print("✅ Login successful!")
                return True
            else:
                print("⚠️  Login may have failed or requires verification")
                print(f"Current URL: {self.driver.current_url}")
                return False
                
        except Exception as e:
            print(f"❌ Login failed: {str(e)}")
            return False
    
    def send_connection_request(self, profile_url, message):
        """
        Send a connection request with personalized note
        Handles multiple scenarios: Connect, Follow, Message, Pending
        
        Args:
            profile_url: LinkedIn profile URL
            message: Personalized connection message (max 300 chars)
            
        Returns:
            dict: Result with success status and details
        """
        print(f"\n📤 Attempting LinkedIn outreach to: {profile_url}")
        
        try:
            # Ensure we're logged in
            if not self.logged_in:
                print("⚠️  Not logged in, attempting login...")
                if not self.login():
                    return {
                        'success': False,
                        'error': 'Login failed'
                    }
            
            # Navigate to profile
            print("🌐 Navigating to profile...")
            self.driver.get(profile_url)
            human_delay(5, 8)  # Increased wait for page load
            
            # Scroll to load page content
            scroll_slowly(self.driver, 300)
            human_delay(3, 5)  # Increased wait after scroll
            
            # Wait for profile actions to be fully loaded
            print("⏳ Waiting for page to fully load...")
            try:
                # Wait for any of the main action buttons to appear
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, "//button[contains(@class, 'pvs-profile-actions')]"))
                )
                human_delay(2, 3)  # Extra wait after elements appear
            except TimeoutException:
                print("  ⚠️  Page load took longer than expected, continuing anyway...")
            
            # Check what action is available
            print("🔍 Analyzing available actions...")
            
            # Try to find different buttons in order of preference
            action_result = None
            
            # 1. Try CONNECT button (best option)
            action_result = self._try_connect_button(message)
            if action_result:
                return action_result
            
            # 2. Try FOLLOW button (if Connect not available)
            action_result = self._try_follow_button()
            if action_result:
                return action_result
            
            # 3. Check if PENDING (already sent request)
            action_result = self._check_pending_status()
            if action_result:
                return action_result
            
            # 4. Try MESSAGE button (already connected)
            action_result = self._try_message_button(message)
            if action_result:
                return action_result
            
            # 5. Check if already connected (no action available)
            if self._check_already_connected():
                return {
                    'success': True,
                    'action_taken': 'already_connected',
                    'message': 'Already connected to this person',
                    'profile_url': profile_url
                }
            
            # No action available
            return {
                'success': False,
                'error': 'No action available - profile may be private or restricted',
                'profile_url': profile_url
            }
                
        except Exception as e:
            print(f"❌ Error during outreach: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'profile_url': profile_url
            }
    
    def _try_connect_button(self, message):
        """
        Try to click Connect button
        LinkedIn shows Connect in two places:
        1. As a visible button on the profile (Pattern A)
        2. Hidden inside "More" dropdown (Pattern B)
        
        We check BOTH locations!
        """
        try:
            print("  🔎 Looking for 'Connect' option...")
            
            # DEBUG: Print all buttons on page
            try:
                all_buttons = self.driver.find_elements(By.TAG_NAME, 'button')
                print(f"  🐛 DEBUG: Found {len(all_buttons)} total buttons on page")
                
                # Print text of first 20 buttons for debugging
                for i, btn in enumerate(all_buttons[:20]):
                    try:
                        btn_text = btn.text.strip() or btn.get_attribute('aria-label') or 'No text'
                        print(f"  🐛 Button {i+1}: '{btn_text[:50]}'")
                    except:
                        continue
            except Exception as e:
                print(f"  ⚠️  Debug info failed: {str(e)[:50]}")
            
            # STEP 1: Check for VISIBLE Connect button first (Pattern A)
            print("  📍 Step 1: Checking for visible Connect button...")
            visible_connect = self._try_visible_connect_button(message)
            if visible_connect:
                return visible_connect
            
            # STEP 2: If no visible Connect, try More dropdown (Pattern B)
            print("  📍 Step 2: No visible Connect button, checking More dropdown...")
            dropdown_connect = self._try_connect_in_dropdown(message)
            if dropdown_connect:
                return dropdown_connect
            
            # No Connect option found anywhere
            print("  ❌ Connect option not found (visible or in dropdown)")
            return None
                
        except Exception as e:
            print(f"  ❌ Error with Connect button: {str(e)}")
            return None
    
    def _try_visible_connect_button(self, message):
        """Check for Connect button that's directly visible on profile"""
        try:
            # Look for visible Connect button (not in dropdown)
            visible_connect_selectors = [
                # Standard Connect button
                "//main//button[.//span[text()='Connect']]",
                "//section[contains(@class, 'pv-top-card')]//button[.//span[text()='Connect']]",
                # Aria label version
                "//button[contains(@aria-label, 'Invite') and contains(@aria-label, 'to connect')]",
                # Simple text match
                "//button[normalize-space(.)='Connect' and not(ancestor::div[contains(@class, 'artdeco-dropdown')])]",
            ]
            
            for i, selector in enumerate(visible_connect_selectors):
                try:
                    print(f"  🔍 Trying visible Connect selector {i+1}/{len(visible_connect_selectors)}...")
                    connect_btn = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    
                    if connect_btn and connect_btn.is_displayed():
                        print(f"  ✅ Found VISIBLE Connect button!")
                        connect_btn.click()
                        human_delay(2, 3)
                        
                        # Try to add personalized note
                        if message and len(message.strip()) > 0:
                            if self._add_connection_note(message):
                                print("  ✅ Added personalized note")
                            else:
                                print("  ⚠️  Couldn't add note, sending without message")
                        
                        # Click Send
                        if self._click_send_button():
                            print("✅ Connection request sent successfully!")
                            return {
                                'success': True,
                                'action_taken': 'connection_request',
                                'profile_url': self.driver.current_url,
                                'message_sent': bool(message)
                            }
                        
                except TimeoutException:
                    continue
                except Exception as e:
                    print(f"  ⚠️  Selector {i+1} error: {str(e)[:50]}")
                    continue
            
            print("  ℹ️  No visible Connect button found")
            return None
            
        except Exception as e:
            print(f"  ⚠️  Error checking visible Connect: {str(e)[:50]}")
            return None
    
    def _try_connect_in_dropdown(self, message):
        """Check for Connect option inside More dropdown"""
        try:
            more_button = None  # Initialize
            
            # CRITICAL: We want the "More" button in the PROFILE ACTIONS area
            # NOT the "More actions" button in the top navigation bar!
            # Profile actions are usually in a section with Message/Follow buttons
            more_selectors = [
                # Simple: just find the More button in main content (not navigation)
                "//main//button[normalize-space(.)='More']",
                # Try finding it near Message/Follow buttons (profile actions)
                "//section[contains(@class, 'pv-top-card')]//button[normalize-space(.)='More']",
                # Look for More button that's AFTER Message button (in same container)
                "//button[contains(., 'Message')]/following-sibling::button[contains(., 'More')]",
                # More specific: Find Message button, go to parent, find More
                "//button[contains(@aria-label, 'Message')]/parent::*/button[contains(., 'More')]",
                # Last resort: any button with just text "More"
                "//button[text()='More' or .//span[text()='More']]",
            ]
            
            for i, selector in enumerate(more_selectors):
                try:
                    print(f"  🔍 Trying selector {i+1}/{len(more_selectors)}: {selector[:60]}...")
                    
                    # Wait for element to be clickable
                    potential_buttons = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_all_elements_located((By.XPATH, selector))
                    )
                    
                    print(f"  🐛 Found {len(potential_buttons)} potential More buttons")
                    
                    # Filter to find the right one
                    for btn in potential_buttons:
                        try:
                            button_text = btn.text or btn.get_attribute('aria-label') or ''
                            print(f"  🐛 Checking button: '{button_text}'")
                            
                            # Skip if it's the navigation "More actions" button
                            if 'actions' in button_text.lower():
                                print(f"  ⚠️  Skipping navigation button")
                                continue
                            
                            # This looks like the profile More button!
                            if 'More' in button_text or 'more' in button_text.lower():
                                # Make sure it's clickable
                                if btn.is_displayed() and btn.is_enabled():
                                    more_button = btn
                                    print(f"  ✅ Found correct 'More' button: '{button_text}'")
                                    break
                        except Exception as e:
                            print(f"  ⚠️  Error checking button: {str(e)[:30]}")
                            continue
                    
                    if more_button:
                        break
                        
                except TimeoutException:
                    print(f"  ❌ Selector {i+1} timed out")
                    continue
                except Exception as e:
                    print(f"  ❌ Selector {i+1} error: {str(e)[:50]}")
                    continue
            
            if not more_button:
                print("  ❌ 'More' button not found after trying all selectors")
                print("  💡 This might mean:")
                print("     - Page not fully loaded (wait longer)")
                print("     - Already connected (no Connect option available)")
                print("     - Different UI structure (LinkedIn A/B testing)")
                return None
            
            # Click "More" to reveal dropdown
            print("  ✅ Found 'More' button, clicking to reveal options...")
            
            # Save the location of the More button we're clicking
            more_button_location = more_button.location
            
            more_button.click()
            human_delay(2, 4)  # Wait for dropdown animation
            
            # Additional wait for dropdown animation to complete
            print("  ⏳ Waiting for dropdown to fully load...")
            human_delay(1, 2)
            
            # DEBUG: Look for dropdown that appeared NEAR the More button we clicked
            try:
                print("  🐛 DEBUG: Checking dropdown contents...")
                
                # Find the dropdown that's actually visible and near our More button
                # Use a more specific selector that gets ONLY the open dropdown
                dropdown_items = self.driver.find_elements(
                    By.XPATH, 
                    "//div[contains(@class, 'artdeco-dropdown__content') and contains(@class, 'is-open')]//span"
                )
                
                # If that doesn't work, try finding items in ANY currently visible dropdown menu
                if len(dropdown_items) == 0:
                    dropdown_items = self.driver.find_elements(
                        By.XPATH,
                        "//div[@role='menu' and not(contains(@style, 'display: none'))]//span"
                    )
                
                print(f"  🐛 Found {len(dropdown_items)} items in open dropdown")
                
                # Print ALL items we find (not just first 10)
                for i, item in enumerate(dropdown_items):
                    try:
                        item_text = item.text.strip()
                        if item_text and len(item_text) > 0:
                            print(f"  🐛 Dropdown item {i+1}: '{item_text}'")
                    except:
                        continue
                        
            except Exception as e:
                print(f"  ⚠️  Debug failed: {str(e)[:100]}")
            
            # Now look for "Connect" in the dropdown
            print("  📍 Looking for 'Connect' in dropdown menu...")
            connect_option = None
            
            # Key insight: Look for Connect in the VISIBLE dropdown menu only
            connect_selectors = [
                # Look in dropdown that's currently open (has 'is-open' class)
                "//div[contains(@class, 'artdeco-dropdown__content') and contains(@class, 'is-open')]//span[text()='Connect']",
                "//div[contains(@class, 'artdeco-dropdown__content') and contains(@class, 'is-open')]//div[text()='Connect']",
                # Look in any visible menu role element
                "//div[@role='menu' and not(contains(@style, 'display: none'))]//span[text()='Connect']",
                # Try the clickable parent
                "//div[contains(@class, 'artdeco-dropdown__content') and contains(@class, 'is-open')]//span[text()='Connect']/..",
                # Try even broader - any currently visible dropdown
                "//div[contains(@class, 'artdeco-dropdown') and not(contains(@class, 'ember-view'))]//span[text()='Connect']",
                # Last resort: just find any Connect that's visible
                "//span[text()='Connect' and not(ancestor::*[contains(@style, 'display: none')])]",
            ]
            
            for i, selector in enumerate(connect_selectors):
                try:
                    print(f"  🔍 Trying Connect selector {i+1}/{len(connect_selectors)}...")
                    connect_option = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    if connect_option:
                        print(f"  ✅ Found 'Connect' with selector #{i+1}")
                        break
                except TimeoutException:
                    print(f"  ❌ Selector {i+1} failed")
                    continue
            
            if not connect_option:
                print("  ❌ 'Connect' option not found in dropdown")
                # Close the dropdown by pressing Escape
                from selenium.webdriver.common.keys import Keys
                self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                return None
            
            print("  ✅ Found 'Connect' option, clicking...")
            connect_option.click()
            human_delay(2, 3)
            
            # Try to add personalized note
            if message and len(message.strip()) > 0:
                if self._add_connection_note(message):
                    print("  ✅ Added personalized note")
                else:
                    print("  ⚠️  Couldn't add note, sending without message")
            
            # Click Send
            if self._click_send_button():
                print("✅ Connection request sent successfully!")
                return {
                    'success': True,
                    'action_taken': 'connection_request',
                    'profile_url': self.driver.current_url,
                    'message_sent': bool(message)
                }
            else:
                return {
                    'success': False,
                    'error': 'Could not click Send button'
                }
                
        except Exception as e:
            print(f"  ❌ Error with Connect button: {str(e)}")
            return None
    
    def _try_follow_button(self):
        """Try to click Follow button (for creator/influencer profiles)"""
        try:
            print("  🔎 Looking for 'Follow' button...")
            
            follow_selectors = [
                "//button[.//span[text()='Follow']]",
                "//button[contains(@aria-label, 'Follow')]",
                "//button[contains(., 'Follow') and not(contains(., 'Following'))]",
            ]
            
            follow_button = None
            for selector in follow_selectors:
                try:
                    follow_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    if follow_button:
                        break
                except TimeoutException:
                    continue
            
            if not follow_button:
                print("  ❌ 'Follow' button not found")
                return None
            
            print("  ✅ Found 'Follow' button, clicking...")
            follow_button.click()
            human_delay(2, 3)
            
            print("✅ Successfully followed this profile!")
            return {
                'success': True,
                'action_taken': 'follow',
                'profile_url': self.driver.current_url,
                'message_sent': False,
                'note': 'Profile set to Follow mode - sent follow instead of connection'
            }
                
        except Exception as e:
            print(f"  ❌ Error with Follow button: {str(e)}")
            return None
    
    def _check_pending_status(self):
        """Check if connection request is already pending"""
        try:
            print("  🔎 Checking for pending status...")
            
            pending_selectors = [
                "//button[.//span[text()='Pending']]",
                "//button[contains(@aria-label, 'Pending')]",
                "//span[contains(text(), 'Pending')]",
            ]
            
            for selector in pending_selectors:
                try:
                    pending_element = self.driver.find_element(By.XPATH, selector)
                    if pending_element:
                        print("  ℹ️  Connection request already pending")
                        return {
                            'success': True,
                            'action_taken': 'already_pending',
                            'message': 'Connection request already sent (pending)',
                            'profile_url': self.driver.current_url
                        }
                except NoSuchElementException:
                    continue
            
            print("  ❌ Not pending")
            return None
                
        except Exception as e:
            print(f"  ❌ Error checking pending: {str(e)}")
            return None
    
    def _try_message_button(self, message_text):
        """Try to send a message (if already connected)"""
        try:
            print("  🔎 Looking for 'Message' button...")
            
            message_selectors = [
                "//button[.//span[text()='Message']]",
                "//button[contains(@aria-label, 'Message')]",
                "//a[contains(@href, '/messaging/')]",
            ]
            
            message_button = None
            for selector in message_selectors:
                try:
                    message_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    if message_button:
                        break
                except TimeoutException:
                    continue
            
            if not message_button:
                print("  ❌ 'Message' button not found")
                return None
            
            print("  ✅ Found 'Message' button (already connected)")
            
            # Don't actually send message for now - just report that we could
            # In future, we can implement actual message sending here
            
            print("✅ Already connected - can send direct message!")
            return {
                'success': True,
                'action_taken': 'already_connected',
                'message': 'Already connected to this person - use messaging instead',
                'profile_url': self.driver.current_url,
                'can_message': True
            }
                
        except Exception as e:
            print(f"  ❌ Error with Message button: {str(e)}")
            return None
    
    def _check_already_connected(self):
        """Check if we're already connected (no action buttons)"""
        try:
            # Look for "Message" or other indicators of connection
            indicators = [
                "//span[contains(text(), 'You are connected')]",
                "//div[contains(@class, 'pv-top-card--is-connected')]",
            ]
            
            for selector in indicators:
                try:
                    element = self.driver.find_element(By.XPATH, selector)
                    if element:
                        return True
                except NoSuchElementException:
                    continue
            
            return False
                
        except:
            return False
    
    def _add_connection_note(self, message):
        """Add personalized note to connection request"""
        try:
            # Look for "Add a note" button
            add_note_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Add a note')]"))
            )
            add_note_button.click()
            human_delay(1, 2)
            
            # Find message textarea
            message_field = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, 'custom-message'))
            )
            
            # Clear and type message
            message_field.clear()
            human_delay(0.5, 1)
            human_type(message_field, message)
            human_delay(2, 3)
            
            return True
            
        except Exception as e:
            print(f"    ⚠️  Could not add note: {str(e)}")
            return False
    
    def _click_send_button(self):
        """Click the Send/Send invitation button"""
        try:
            send_selectors = [
                "//button[contains(@aria-label, 'Send') and not(contains(@aria-label, 'without'))]",
                "//button[.//span[text()='Send']]",
                "//button[contains(., 'Send now')]",
                "//button[contains(., 'Send invitation')]",
            ]
            
            send_button = None
            for selector in send_selectors:
                try:
                    send_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    if send_button:
                        break
                except TimeoutException:
                    continue
            
            if not send_button:
                print("    ❌ Could not find Send button")
                return False
            
            send_button.click()
            human_delay(3, 5)
            return True
            
        except Exception as e:
            print(f"    ❌ Error clicking Send: {str(e)}")
            return False
    
    def close(self):
        """Close the browser"""
        if self.driver:
            print("🔒 Closing browser...")
            self.driver.quit()
            self.logged_in = False
            print("✅ Browser closed")