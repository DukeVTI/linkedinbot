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
        
        # Prevent page load hangs and timeouts
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-renderer-backgrounding')
        options.add_argument('--disable-features=TranslateUI')
        options.add_argument('--disable-features=BlinkGenPropertyTrees')
        
        # Page loading strategy - don't wait for all resources
        options.page_load_strategy = 'normal'  # or 'eager' for faster loads
        
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
        """
        Check if we're currently logged in to LinkedIn
        
        Uses a two-step verification:
        1. Check URL (quick check for redirects)
        2. Verify logged-in UI elements exist
        
        Returns:
            bool: True if logged in, False otherwise
        """
        try:
            print("🔐 Checking login status...")
            
            # Step 1: Navigate to feed with timeout handling
            print("📍 Navigating to LinkedIn feed...")
            
            try:
                self.driver.get('https://www.linkedin.com/feed')
            except Exception as e:
                # Page load timeout - check if we can still interact
                if 'timeout' in str(e).lower():
                    print("⚠️  Page load timed out, checking if page is usable...")
                    try:
                        # Check if page loaded enough to be usable
                        current_url = self.driver.current_url
                        print(f"📍 Page partially loaded: {current_url}")
                    except:
                        print("❌ Page completely unresponsive")
                        self.logged_in = False
                        return False
                else:
                    raise
            
            # Wait for page to load and any redirects to complete
            human_delay(3, 5)
            
            # Step 2: Check current URL (quick detection of redirects)
            try:
                current_url = self.driver.current_url
                print(f"📍 Current URL: {current_url}")
            except Exception as e:
                print(f"❌ Cannot get current URL: {str(e)[:50]}")
                self.logged_in = False
                return False
            
            # Check if we got redirected to login page
            if 'login' in current_url.lower() or '/uas/login' in current_url:
                print("❌ Redirected to login page - not logged in")
                self.logged_in = False
                return False
            
            # Check if we're on a security checkpoint
            if 'checkpoint' in current_url.lower():
                print("⚠️  Security checkpoint detected - manual verification needed")
                print("   Please complete the verification in the browser window")
                self.logged_in = False
                return False
            
            # Check if we're still on an auth-related page
            if '/authwall' in current_url or '/signup' in current_url:
                print("❌ On authentication page - not logged in")
                self.logged_in = False
                return False
            
            # Step 3: Verify we're on a logged-in page and elements are present
            # Multiple methods to verify login status
            
            # Method 1: Check for the "Me" button (profile dropdown)
            try:
                print("  🔍 Looking for 'Me' button (profile menu)...")
                me_button = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((
                        By.XPATH, 
                        "//button[contains(@class, 'global-nav__me') or contains(@aria-label, 'Me') or contains(@id, 'ember')]"
                    ))
                )
                
                if me_button and me_button.is_displayed():
                    print("  ✅ Found 'Me' button - user is logged in!")
                    self.logged_in = True
                    return True
                    
            except TimeoutException:
                print("  ⚠️  'Me' button not found, trying alternative checks...")
            except Exception as e:
                print(f"  ⚠️  Error checking 'Me' button: {str(e)[:50]}")
            
            # Method 2: Look for navigation bar (backup check)
            try:
                print("  🔍 Looking for navigation bar...")
                nav_bar = self.driver.find_element(
                    By.XPATH,
                    "//nav[contains(@class, 'global-nav')]"
                )
                
                if nav_bar and nav_bar.is_displayed():
                    print("  ✅ Found navigation bar - appears logged in!")
                    self.logged_in = True
                    return True
                    
            except NoSuchElementException:
                print("  ⚠️  Navigation bar not found...")
            except Exception as e:
                print(f"  ⚠️  Error checking navigation: {str(e)[:50]}")
            
            # Method 3: Check for search bar (only visible when logged in)
            try:
                print("  🔍 Looking for search bar...")
                search_bar = self.driver.find_element(
                    By.XPATH,
                    "//input[contains(@placeholder, 'Search') or contains(@aria-label, 'Search')]"
                )
                
                if search_bar and search_bar.is_displayed():
                    print("  ✅ Found search bar - user is logged in!")
                    self.logged_in = True
                    return True
                    
            except NoSuchElementException:
                print("  ⚠️  Search bar not found...")
            except Exception as e:
                print(f"  ⚠️  Error checking search bar: {str(e)[:50]}")
            
            # Method 4: Check if we're on feed and can see posts
            if 'feed' in current_url.lower():
                try:
                    print("  🔍 Checking for feed posts...")
                    feed_posts = self.driver.find_elements(
                        By.XPATH,
                        "//div[contains(@class, 'feed-shared-update-v2')]"
                    )
                    
                    if len(feed_posts) > 0:
                        print(f"  ✅ Found {len(feed_posts)} feed posts - user is logged in!")
                        self.logged_in = True
                        return True
                        
                except Exception as e:
                    print(f"  ⚠️  Error checking feed posts: {str(e)[:50]}")
            
            # If we got here, couldn't confirm login
            print("❌ Could not verify login status - no logged-in elements found")
            print(f"   Current URL: {current_url}")
            print("   This usually means:")
            print("   - Session expired")
            print("   - Chrome profile doesn't have valid session")
            print("   - Page not fully loaded")
            print("   - Manual login required")
            
            self.logged_in = False
            return False
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Error checking login status: {error_msg[:100]}")
            
            # Give more specific guidance based on error type
            if 'timeout' in error_msg.lower():
                print("   💡 Timeout error suggests:")
                print("      - Chrome profile may be corrupted")
                print("      - Network issues preventing LinkedIn from loading")
                print("      - Try deleting chrome_bot_profile folder and re-logging in")
            
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
        
        FLOW:
        1. Navigate to profile
        2. Detect current status (pending/connected/following)
        3. If no status, try to connect (visible button or dropdown)
        4. If can't connect, try to follow
        5. Return appropriate result
        
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
            human_delay(5, 8)
            
            # Scroll to load page content
            scroll_slowly(self.driver, 300)
            human_delay(3, 5)
            
            # Wait for profile actions to be fully loaded
            print("⏳ Waiting for page to fully load...")
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, "//button[contains(@class, 'pvs-profile-actions')]"))
                )
                human_delay(2, 3)
            except TimeoutException:
                print("  ⚠️  Page load took longer than expected, continuing anyway...")
            
            # STEP 1: Check what action is available
            print("🔍 Analyzing available actions...")
            
            # Print all buttons for debugging
            try:
                all_buttons = self.driver.find_elements(By.TAG_NAME, 'button')
                print(f"  🐛 DEBUG: Found {len(all_buttons)} total buttons on page")
                
                for i, btn in enumerate(all_buttons[:20]):
                    try:
                        btn_text = btn.text.strip() or btn.get_attribute('aria-label') or 'No text'
                        print(f"  🐛 Button {i+1}: '{btn_text[:50]}'")
                    except:
                        continue
            except Exception as e:
                print(f"  ⚠️  Debug info failed: {str(e)[:50]}")
            
            # STEP 2: FIRST check if there's already a status (pending/connected/following)
            # This prevents trying to connect when we shouldn't
            print("  📍 STEP 1: Checking existing relationship status...")
            status_result = self._detect_relationship_status()
            if status_result:
                # Found existing status - return it
                return status_result
            
            # STEP 3: No existing status - try to connect
            print("  📍 STEP 2: No existing relationship - looking for Connect option...")
            connect_result = self._try_connect_button(message)
            if connect_result:
                return connect_result
            
            # STEP 4: Can't connect - try to follow
            print("  📍 STEP 3: Connect not available - trying Follow...")
            follow_result = self._try_follow_button()
            if follow_result:
                return follow_result
            
            # STEP 5: No action available
            print("  ❌ No action available on this profile")
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
    
    def _detect_relationship_status(self):
        """
        Detect if there's already a relationship with this person
        
        Returns:
            dict if status found (pending/connected/following), None if no status
        """
        try:
            # Check for PENDING connection request
            print("    🔍 Checking for Pending status...")
            pending_selectors = [
                "//button[contains(., 'Pending') or contains(@aria-label, 'Pending')]",
                "//button[contains(@aria-label, 'withdraw')]",
            ]
            
            for selector in pending_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed():
                            element_text = element.text or element.get_attribute('aria-label') or ''
                            print(f"    ✅ FOUND: Connection request already PENDING")
                            print(f"    📝 Element text: '{element_text[:100]}'")
                            
                            return {
                                'success': True,
                                'action_taken': 'already_pending',
                                'message': 'Connection request already pending',
                                'profile_url': self.driver.current_url,
                                'skip_reason': 'Connection request already sent and pending'
                            }
                except:
                    continue
            
            # Check for ALREADY CONNECTED
            print("    🔍 Checking for Already Connected status...")
            # If Message button exists but NO Connect/Follow/Pending, they're connected
            try:
                message_btn = self.driver.find_elements(By.XPATH, "//button[normalize-space(.)='Message']")
                connect_btn = self.driver.find_elements(By.XPATH, "//button[normalize-space(.)='Connect']")
                follow_btn = self.driver.find_elements(By.XPATH, "//button[normalize-space(.)='Follow' or normalize-space(.)='Following']")
                pending_btn = self.driver.find_elements(By.XPATH, "//button[contains(., 'Pending')]")
                
                has_message = any(btn.is_displayed() for btn in message_btn)
                has_connect = any(btn.is_displayed() for btn in connect_btn)
                has_follow = any(btn.is_displayed() for btn in follow_btn)
                has_pending = any(btn.is_displayed() for btn in pending_btn)
                
                if has_message and not has_connect and not has_follow and not has_pending:
                    print(f"    ✅ FOUND: Already CONNECTED (Message only, no Connect/Follow/Pending)")
                    
                    return {
                        'success': True,
                        'action_taken': 'already_connected',
                        'message': 'Already connected to this person',
                        'profile_url': self.driver.current_url,
                        'skip_reason': 'Already in network'
                    }
            except:
                pass
            
            # Check for FOLLOWING
            print("    🔍 Checking for Following status...")
            following_selectors = [
                "//button[contains(., 'Following') or contains(@aria-label, 'Following')]",
            ]
            
            for selector in following_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed():
                            element_text = element.text or element.get_attribute('aria-label') or ''
                            print(f"    ✅ FOUND: Already FOLLOWING this person")
                            print(f"    📝 Element text: '{element_text[:100]}'")
                            
                            return {
                                'success': True,
                                'action_taken': 'already_following',
                                'message': 'Already following this person',
                                'profile_url': self.driver.current_url,
                                'skip_reason': 'Already following (creator/influencer profile)'
                            }
                except:
                    continue
            
            # No status found
            print("    ℹ️  No existing relationship status detected")
            return None
            
        except Exception as e:
            print(f"    ⚠️  Error detecting status: {str(e)[:100]}")
            return None
    
    def _try_connect_button(self, message):
        """
        Try to click Connect button
        LinkedIn shows Connect in two places:
        1. As a visible button on the profile (Pattern A)
        2. Hidden inside "More" dropdown (Pattern B)
        
        Status has already been checked by caller - this only looks for Connect button
        """
        try:
            print("  🔎 Looking for 'Connect' option...")
            
            # STEP 1: Check for VISIBLE Connect button first (Pattern A)
            print("    📍 Trying visible Connect button...")
            visible_connect = self._try_visible_connect_button(message)
            if visible_connect:
                return visible_connect
            
            # STEP 2: Try More dropdown (Pattern B)
            print("    📍 Trying More dropdown...")
            dropdown_connect = self._try_connect_in_dropdown(message)
            if dropdown_connect:
                return dropdown_connect
            
            # No Connect option found anywhere
            print("    ❌ Connect option not found (visible or in dropdown)")
            return None
                
        except Exception as e:
            print(f"  ❌ Error with Connect button: {str(e)}")
            return None
    
    def _try_visible_connect_button(self, message):
        """
        Check for Connect button that's directly visible on the TARGET profile
        
        Strategy: Use simple selectors, then filter by position to avoid sidebar
        """
        try:
            print("  📍 Step 1: Checking for visible Connect button ON TARGET PROFILE...")
            
            # SIMPLE selectors that find ANY Connect button, then we filter by position
            visible_connect_selectors = [
                # Simple text match - finds all Connect buttons
                "//button[normalize-space(.)='Connect']",
                
                # Aria label version
                "//button[contains(@aria-label, 'Invite') and contains(@aria-label, 'to connect')]",
                
                # With span child
                "//button[.//span[normalize-space()='Connect']]",
                
                # Connect button that's a sibling of Message
                "//button[normalize-space(.)='Message']/following-sibling::button[normalize-space(.)='Connect']",
            ]
            
            # Try each selector
            for i, selector in enumerate(visible_connect_selectors):
                try:
                    print(f"  🔍 Trying visible Connect selector {i+1}/{len(visible_connect_selectors)}...")
                    
                    # Find all matching buttons
                    potential_buttons = self.driver.find_elements(By.XPATH, selector)
                    
                    print(f"    🐛 Found {len(potential_buttons)} potential Connect buttons with this selector")
                    
                    if len(potential_buttons) == 0:
                        continue
                    
                    # NOW FILTER BY POSITION - this is the KEY part!
                    connect_btn = None
                    for btn_idx, btn in enumerate(potential_buttons):
                        try:
                            # Check if button is displayed
                            if not btn.is_displayed():
                                print(f"    ⚠️  Button {btn_idx+1} not displayed, skipping...")
                                continue
                            
                            # Get button info for debugging
                            btn_text = btn.text or btn.get_attribute('aria-label') or 'No text'
                            
                            # Get button position
                            location = btn.location
                            y_position = location['y']
                            x_position = location['x']
                            
                            print(f"    🐛 Button {btn_idx+1}: text='{btn_text}', position: x={x_position}, y={y_position}")
                            
                            # CRITICAL FILTER: Profile Connect buttons are at TOP of page
                            # Sidebar "More profiles for you" buttons are LOWER
                            
                            # Profile header is typically y < 600px
                            # But let's be generous and allow up to y < 700px
                            if y_position > 700:
                                print(f"    ⚠️  Button too far down (y={y_position}), likely sidebar - SKIPPING")
                                continue
                            
                            # Also check it's not too far right (sidebar is on right side)
                            # Profile buttons are typically x < 800px
                            if x_position > 1000:
                                print(f"    ⚠️  Button too far right (x={x_position}), likely sidebar - SKIPPING")
                                continue
                            
                            # Found a good candidate!
                            connect_btn = btn
                            print(f"    ✅ Found VALID Connect button at position x={x_position}, y={y_position}")
                            break
                            
                        except Exception as e:
                            print(f"    ⚠️  Error checking button {btn_idx+1}: {str(e)[:50]}")
                            continue
                    
                    if not connect_btn:
                        print(f"    ❌ No valid Connect button after position filtering")
                        continue
                    
                    # Found the right button! Click it!
                    print(f"  ✅ Found VISIBLE Connect button on TARGET PROFILE!")
                    print(f"  🖱️  Clicking Connect button...")
                    connect_btn.click()
                    human_delay(2, 3)
                    
                    # Track whether message was actually sent
                    message_actually_sent = False
                    note_add_method = None
                    
                    # Try to add personalized note
                    if message and len(message.strip()) > 0:
                        note_result = self._add_connection_note(message)
                        
                        if note_result['success']:
                            print(f"  ✅ Added personalized note (method: {note_result['method']})")
                            message_actually_sent = True
                            note_add_method = note_result['method']
                        else:
                            print(f"  ⚠️  Failed to add note: {note_result['error']}")
                            print("  ⚠️  Sending connection request WITHOUT personalized message")
                            message_actually_sent = False
                    else:
                        print("  ℹ️  No message provided, sending connection without note")
                    
                    # Click Send button (pass whether note was added)
                    if self._click_send_button(note_was_added=message_actually_sent):
                        print("✅ Connection request sent successfully!")
                        return {
                            'success': True,
                            'action_taken': 'connection_request',
                            'profile_url': self.driver.current_url,
                            'message_sent': message_actually_sent,
                            'note_method': note_add_method,
                            'message_provided': bool(message and len(message.strip()) > 0)
                        }
                    
                except TimeoutException:
                    print(f"  ❌ Selector {i+1} timed out")
                    continue
                except Exception as e:
                    print(f"  ⚠️  Selector {i+1} error: {str(e)[:100]}")
                    continue
            
            print("  ℹ️  No visible Connect button found on target profile")
            print("  💡 This usually means:")
            print("     - Connect is in the More dropdown (will try that next)")
            print("     - Already connected to this person")
            print("     - This is a creator/influencer (Follow only)")
            return None
            
        except Exception as e:
            print(f"  ❌ Error checking visible Connect: {str(e)[:100]}")
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
            message_actually_sent = False
            note_add_method = None
            
            if message and len(message.strip()) > 0:
                note_result = self._add_connection_note(message)
                
                if note_result['success']:
                    print(f"  ✅ Added personalized note (method: {note_result['method']})")
                    message_actually_sent = True
                    note_add_method = note_result['method']
                else:
                    print(f"  ⚠️  Failed to add note: {note_result['error']}")
                    print("  ⚠️  Sending connection request WITHOUT personalized message")
                    message_actually_sent = False
            else:
                print("  ℹ️  No message provided, sending connection without note")
            
            # Click Send (pass whether note was added)
            if self._click_send_button(note_was_added=message_actually_sent):
                print("✅ Connection request sent successfully!")
                return {
                    'success': True,
                    'action_taken': 'connection_request',
                    'profile_url': self.driver.current_url,
                    'message_sent': message_actually_sent,  # ACCURATE status!
                    'note_method': note_add_method,
                    'message_provided': bool(message and len(message.strip()) > 0)
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
    
    def _add_connection_note(self, message):
        """
        Add personalized note to connection request
        
        ROBUST VERSION with multiple strategies and detailed verification
        
        Returns:
            dict: {
                'success': bool - Whether note was successfully added
                'method': str - Which method succeeded
                'error': str - Error message if failed
            }
        """
        print(f"  📝 Attempting to add connection note ({len(message)} characters)...")
        
        # Verify we have a valid message
        if not message or len(message.strip()) == 0:
            return {
                'success': False,
                'method': None,
                'error': 'No message provided'
            }
        
        # Check message length (LinkedIn limit is 300 characters)
        if len(message) > 300:
            print(f"  ⚠️  Message too long ({len(message)} chars), truncating to 300...")
            message = message[:297] + "..."
        
        # Strategy 1: Click "Add a note" button to expand text area
        result = self._strategy_click_add_note_button(message)
        if result['success']:
            return result
        
        # Strategy 2: Look for already-visible text area (sometimes it's pre-expanded)
        result = self._strategy_find_visible_textarea(message)
        if result['success']:
            return result
        
        # Strategy 3: Try alternative button selectors
        result = self._strategy_alternative_add_note_button(message)
        if result['success']:
            return result
        
        # All strategies failed
        print("  ❌ All strategies to add note failed")
        return {
            'success': False,
            'method': None,
            'error': 'All note-adding strategies failed'
        }
    
    def _strategy_click_add_note_button(self, message):
        """Strategy 1: Click 'Add a note' button"""
        try:
            print("    🔍 Strategy 1: Looking for 'Add a note' button...")
            
            # Multiple selectors for the "Add a note" button
            add_note_selectors = [
                "//button[contains(text(), 'Add a note')]",
                "//button[@aria-label='Add a note']",
                "//button[contains(@class, 'add-note')]",
                "//button[.//span[contains(text(), 'Add a note')]]",
                "//a[contains(text(), 'Add a note')]",  # Sometimes it's a link
            ]
            
            add_note_button = None
            for i, selector in enumerate(add_note_selectors):
                try:
                    add_note_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    if add_note_button and add_note_button.is_displayed():
                        print(f"    ✅ Found 'Add a note' button (selector {i+1})")
                        break
                except TimeoutException:
                    continue
            
            if not add_note_button:
                return {
                    'success': False,
                    'method': 'click_add_note_button',
                    'error': 'Add a note button not found'
                }
            
            # Click the button
            print("    🖱️  Clicking 'Add a note' button...")
            add_note_button.click()
            human_delay(1, 2)
            
            # Now find and fill the text area
            return self._fill_message_textarea(message, 'click_add_note_button')
            
        except Exception as e:
            return {
                'success': False,
                'method': 'click_add_note_button',
                'error': str(e)[:100]
            }
    
    def _strategy_find_visible_textarea(self, message):
        """Strategy 2: Text area is already visible (no button click needed)"""
        try:
            print("    🔍 Strategy 2: Looking for already-visible text area...")
            
            return self._fill_message_textarea(message, 'visible_textarea')
            
        except Exception as e:
            return {
                'success': False,
                'method': 'visible_textarea',
                'error': str(e)[:100]
            }
    
    def _strategy_alternative_add_note_button(self, message):
        """Strategy 3: Try clicking anywhere in the note area to expand it"""
        try:
            print("    🔍 Strategy 3: Trying alternative expansion methods...")
            
            # Sometimes clicking on the container expands it
            container_selectors = [
                "//div[contains(@class, 'send-invite')]",
                "//div[contains(@class, 'invitation-modal')]",
                "//div[contains(text(), 'Add a note')]",
            ]
            
            for selector in container_selectors:
                try:
                    container = self.driver.find_element(By.XPATH, selector)
                    if container and container.is_displayed():
                        print(f"    🖱️  Clicking container to expand...")
                        container.click()
                        human_delay(1, 2)
                        
                        # Try to fill text area
                        result = self._fill_message_textarea(message, 'alternative_click')
                        if result['success']:
                            return result
                except:
                    continue
            
            return {
                'success': False,
                'method': 'alternative_click',
                'error': 'Could not expand note area'
            }
            
        except Exception as e:
            return {
                'success': False,
                'method': 'alternative_click',
                'error': str(e)[:100]
            }
    
    def _fill_message_textarea(self, message, method_name):
        """
        Find and fill the message text area
        
        Args:
            message: The message to type
            method_name: Name of the strategy that called this
            
        Returns:
            dict with success status
        """
        try:
            print("    📝 Looking for message text area...")
            
            # Multiple selectors for the textarea
            textarea_selectors = [
                "//textarea[@id='custom-message']",
                "//textarea[@name='message']",
                "//textarea[contains(@placeholder, 'Add a note')]",
                "//textarea[contains(@class, 'send-invite__custom-message')]",
                "//textarea[contains(@aria-label, 'Add a note')]",
                "//div[@role='textbox']",  # Sometimes it's a contenteditable div
            ]
            
            message_field = None
            for i, selector in enumerate(textarea_selectors):
                try:
                    message_field = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    if message_field and message_field.is_displayed():
                        print(f"    ✅ Found text area (selector {i+1})")
                        break
                except TimeoutException:
                    continue
            
            if not message_field:
                print("    ❌ Could not find message text area")
                return {
                    'success': False,
                    'method': method_name,
                    'error': 'Message text area not found after expansion'
                }
            
            # Clear any existing text
            print("    🧹 Clearing text area...")
            message_field.clear()
            human_delay(0.3, 0.7)
            
            # Type the message using human-like typing
            print(f"    ⌨️  Typing message ({len(message)} characters)...")
            human_type(message_field, message)
            human_delay(1, 2)
            
            # Verify the message was typed correctly
            typed_text = message_field.get_attribute('value')
            if not typed_text:
                # Try alternative attribute for contenteditable divs
                typed_text = message_field.text
            
            if len(typed_text) < len(message) * 0.9:  # Allow 10% variance
                print(f"    ⚠️  Warning: Only {len(typed_text)}/{len(message)} characters typed")
            
            print(f"    ✅ Successfully typed {len(typed_text)} characters")
            
            return {
                'success': True,
                'method': method_name,
                'error': None
            }
            
        except Exception as e:
            error_msg = str(e)[:100]
            print(f"    ❌ Error filling textarea: {error_msg}")
            return {
                'success': False,
                'method': method_name,
                'error': error_msg
            }
    
    def _click_send_button(self, note_was_added=False):
        """
        Click the Send/Send invitation button
        
        Args:
            note_was_added: Whether a note was successfully added
            
        Returns:
            bool: True if successfully clicked Send, False otherwise
        """
        try:
            print("    📤 Looking for Send button...")
            
            # If note was added, look for regular "Send" button
            # If note was NOT added, we might need to click "Send without a note"
            if note_was_added:
                send_selectors = [
                    "//button[contains(@aria-label, 'Send') and not(contains(@aria-label, 'without'))]",
                    "//button[@aria-label='Send invitation']",
                    "//button[.//span[text()='Send']]",
                    "//button[contains(., 'Send now')]",
                    "//button[text()='Send']",
                ]
            else:
                # When no note, we might see "Send without a note" OR just "Send"
                send_selectors = [
                    "//button[contains(., 'Send without a note')]",
                    "//button[contains(@aria-label, 'Send without')]",
                    "//button[.//span[contains(text(), 'Send')]]",
                    "//button[contains(@aria-label, 'Send')]",
                    "//button[text()='Send']",
                ]
            
            send_button = None
            successful_selector = None
            
            for i, selector in enumerate(send_selectors):
                try:
                    send_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    if send_button and send_button.is_displayed():
                        successful_selector = i + 1
                        print(f"    ✅ Found Send button (selector {successful_selector})")
                        break
                except TimeoutException:
                    continue
            
            if not send_button:
                print("    ❌ Could not find Send button")
                print("    💡 Possible reasons:")
                print("       - Connection limit reached")
                print("       - Modal closed unexpectedly")
                print("       - Page changed")
                return False
            
            # Get button text for logging
            button_text = send_button.text or send_button.get_attribute('aria-label') or 'Send'
            print(f"    🖱️  Clicking '{button_text}' button...")
            
            send_button.click()
            human_delay(2, 4)
            
            # Verify the modal closed (successful send)
            try:
                # Check if the invitation modal is still visible
                modal = self.driver.find_element(
                    By.XPATH,
                    "//div[contains(@class, 'send-invite') or contains(@class, 'artdeco-modal')]"
                )
                if modal and modal.is_displayed():
                    print("    ⚠️  Warning: Modal still visible after clicking Send")
                    # Give it more time
                    human_delay(2, 3)
            except:
                # Modal not found = good! It closed
                pass
            
            print("    ✅ Send button clicked successfully")
            return True
            
        except Exception as e:
            error_msg = str(e)[:100]
            print(f"    ❌ Error clicking Send: {error_msg}")
            return False
            
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