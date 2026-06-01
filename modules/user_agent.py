# modules/user_agent.py
import random

FALLBACK_USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0'
]

try:
    from fake_useragent import UserAgent
    # Исправлено: 'browsers' вместо 'browser'
    ua = UserAgent(browsers=['chrome', 'firefox', 'safari', 'edge'])
    def get_random_user_agent():
        try:
            return ua.random
        except:
            return random.choice(FALLBACK_USER_AGENTS)
except ImportError:
    def get_random_user_agent():
        return random.choice(FALLBACK_USER_AGENTS)