import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration for LinkedIn Bot"""
    
    # LinkedIn Credentials (email for reference only, password optional)
    LINKEDIN_EMAIL = os.getenv('LINKEDIN_EMAIL')
    LINKEDIN_PASSWORD = os.getenv('LINKEDIN_PASSWORD')  # Optional - only for legacy password login
    
    # Bot Settings
    HEADLESS = os.getenv('HEADLESS', 'false').lower() == 'true'
    PORT = int(os.getenv('PORT', 5000))
    USE_CHROME_PROFILE = os.getenv('USE_CHROME_PROFILE', 'false').lower() == 'true'
    
    # Safety Settings
    MAX_DAILY_CONNECTIONS = int(os.getenv('MAX_DAILY_CONNECTIONS', 30))
    MIN_DELAY_SECONDS = int(os.getenv('MIN_DELAY_SECONDS', 120))
    MAX_DELAY_SECONDS = int(os.getenv('MAX_DELAY_SECONDS', 300))
    
    @classmethod
    def validate(cls):
        """Validate that required config is set"""
        if not cls.LINKEDIN_EMAIL:
            print("⚠️  Warning: LINKEDIN_EMAIL not set in .env file")
            print("This is optional but recommended for logging purposes")
        return True
