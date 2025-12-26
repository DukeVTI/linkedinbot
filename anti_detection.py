import time
import random
from selenium.webdriver.common.action_chains import ActionChains

def human_delay(min_seconds=2, max_seconds=5):
    """
    Add random delay to mimic human behavior
    
    Args:
        min_seconds: Minimum delay in seconds
        max_seconds: Maximum delay in seconds
    """
    delay = random.uniform(min_seconds, max_seconds)
    print(f"⏱️  Waiting {delay:.2f} seconds...")
    time.sleep(delay)

def human_type(element, text, min_delay=0.05, max_delay=0.2):
    """
    Type text character by character with random delays
    Mimics human typing speed
    
    Args:
        element: Selenium WebElement to type into
        text: Text to type
        min_delay: Minimum delay between keystrokes (seconds)
        max_delay: Maximum delay between keystrokes (seconds)
    """
    print(f"⌨️  Typing: {text[:50]}{'...' if len(text) > 50 else ''}")
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(min_delay, max_delay))

def random_mouse_movement(driver, element):
    """
    Move mouse to element with random path
    Makes automation look more human
    
    Args:
        driver: Selenium WebDriver instance
        element: Target element to move to
    """
    try:
        actions = ActionChains(driver)
        # Move to a random offset first
        actions.move_by_offset(
            random.randint(-100, 100),
            random.randint(-100, 100)
        )
        # Then move to the actual element
        actions.move_to_element(element)
        actions.perform()
        human_delay(0.5, 1.5)
    except:
        pass  # Silently fail if mouse movement doesn't work

def scroll_slowly(driver, scroll_amount=300):
    """
    Scroll page slowly to mimic human browsing
    
    Args:
        driver: Selenium WebDriver instance
        scroll_amount: Pixels to scroll
    """
    try:
        current_position = driver.execute_script("return window.pageYOffset;")
        
        # Handle None values
        if current_position is None:
            current_position = 0
        if scroll_amount is None:
            scroll_amount = 300
            
        target_position = current_position + scroll_amount
        
        # Scroll in small increments
        while current_position < target_position:
            current_position += random.randint(20, 50)
            driver.execute_script(f"window.scrollTo(0, {current_position});")
            time.sleep(random.uniform(0.1, 0.3))
    except Exception:
        # If scroll fails, just continue
        pass