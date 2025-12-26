#!/usr/bin/env python3
"""
Local test script for LinkedIn bot
Run this to test the bot without n8n

COOKIE-BASED AUTHENTICATION:
This bot uses session cookies instead of passwords.
First time setup: Run setup_cookies() to log in manually and save cookies.
After that: Bot uses saved cookies automatically!
"""

from linkedin_bot import LinkedInBot
from config import Config
import os

def setup_cookies():
    """
    ONE-TIME SETUP: Log in once, Chrome profile remembers forever
    """
    print("\n" + "="*60)
    print("🔐 LOGIN SETUP - ONE-TIME CONFIGURATION")
    print("="*60 + "\n")
    
    bot = LinkedInBot()
    success = bot.manual_login_and_save_cookies()
    
    if success:
        print("\n✅ Setup complete!")
        print("✅ Chrome profile will remember your session")
        print("\n👉 Next: Run test_login() to verify it works")
    else:
        print("\n❌ Setup failed")
        print("Please try again")
    
    bot.close()
    return success

def test_login():
    """Test LinkedIn login using Chrome profile (automatic!)"""
    print("\n" + "="*60)
    print("TEST: Automatic Login via Chrome Profile")
    print("="*60 + "\n")
    
    bot = LinkedInBot()
    success = bot.login()
    
    if success:
        print("\n✅ Login test PASSED")
        print("✅ Bot logged in automatically via Chrome profile!")
    else:
        print("\n❌ Login test FAILED")
        print("👉 Chrome profile doesn't have valid session")
        print("👉 Run setup_cookies() to log in once")
    
    bot.close()
    return success

def test_connection_request():
    """Test sending a connection request"""
    print("\n" + "="*60)
    print("TEST 2: Send Connection Request")
    print("="*60 + "\n")
    
    # REPLACE THESE WITH TEST VALUES
    TEST_PROFILE_URL = "https://www.linkedin.com/in/daniel-oshiguwa-327936340/"
    TEST_MESSAGE = "Hi! I'd love to connect and learn more about your work."
    
    print("⚠️  IMPORTANT: Update TEST_PROFILE_URL and TEST_MESSAGE in test_bot.py")
    print(f"Current test profile: {TEST_PROFILE_URL}")
    
    proceed = input("\nProceed with test? (yes/no): ").strip().lower()
    if proceed != 'yes':
        print("Test cancelled")
        return False
    
    bot = LinkedInBot()
    
    # Login first
    if not bot.login():
        print("❌ Could not login")
        bot.close()
        return False
    
    # Send connection request (or follow, or detect existing connection)
    result = bot.send_connection_request(TEST_PROFILE_URL, TEST_MESSAGE)
    
    print("\n" + "="*60)
    print("RESULT:")
    print("="*60)
    print(f"Success: {result['success']}")
    print(f"Profile: {result.get('profile_url', 'N/A')}")
    
    if result['success']:
        action = result.get('action_taken', 'unknown')
        print(f"Action Taken: {action}")
        
        if action == 'connection_request':
            print(f"Message sent: {result.get('message_sent', False)}")
            print("\n✅ Connection request sent successfully!")
        elif action == 'follow':
            print(f"Note: {result.get('note', '')}")
            print("\n✅ Successfully followed profile!")
        elif action == 'already_pending':
            print(f"Message: {result.get('message', '')}")
            print("\n✅ Connection request already pending!")
        elif action == 'already_connected':
            print(f"Message: {result.get('message', '')}")
            print(f"Can message: {result.get('can_message', False)}")
            print("\n✅ Already connected to this person!")
        else:
            print(f"Message: {result.get('message', '')}")
            print("\n✅ Action completed!")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
        print("\n❌ Action failed!")
    
    print("="*60 + "\n")
    
    bot.close()
    return result['success']

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 LINKEDIN BOT - LOCAL TESTING")
    print("="*60)
    print("\nUsing persistent Chrome profile for automatic login!")
    print("="*60 + "\n")
    
    # Check if we need first-time setup
    profile_dir = os.path.join(os.getcwd(), 'chrome_bot_profile')
    
    if not os.path.exists(profile_dir) or not os.path.exists(os.path.join(profile_dir, 'Default')):
        print("⚠️  Chrome profile not initialized yet!")
        print("\n👉 FIRST TIME SETUP REQUIRED")
        print("\nThis is a ONE-TIME setup that takes 30 seconds.")
        print("You'll log in once, and Chrome will remember your session.")
        print("\n" + "="*60 + "\n")
        
        proceed = input("Run login setup now? (yes/no): ").strip().lower()
        if proceed != 'yes':
            print("\nSetup cancelled. Run this script again when ready.")
            return
        
        # Run login setup
        if not setup_cookies():
            print("\n❌ Setup failed. Please try again.")
            return
        
        print("\n" + "="*60)
        print("✅ SETUP COMPLETE!")
        print("="*60 + "\n")
    
    # Test automatic login
    print("Testing automatic login via Chrome profile...\n")
    login_ok = test_login()
    
    if not login_ok:
        print("\n❌ Automatic login failed")
        print("👉 Chrome profile may not have valid session")
        print("👉 Run setup_cookies() to log in again")
        return
    
    # Test connection request
    print("\n" + "="*60)
    input("Press ENTER to test sending a connection request (or Ctrl+C to cancel)...")
    test_connection_request()
    
    print("\n✅ All tests complete!\n")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests cancelled by user\n")
    except Exception as e:
        print(f"\n❌ Error: {e}\n")