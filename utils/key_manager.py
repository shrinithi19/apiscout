import os
import itertools
from dotenv import load_dotenv

load_dotenv()

def get_api_keys() -> list[str]:
    """Loads all available Gemini API keys from .env"""
    keys = []
    i = 1
    while True:
        key = os.getenv(f"GEMINI_API_KEY_{i}")
        if not key:
            break
        keys.append(key)
        i += 1

    # Fallback to single key if numbered keys not found
    if not keys:
        single = os.getenv("GEMINI_API_KEY")
        if single:
            keys.append(single)

    if not keys:
        raise ValueError("No Gemini API keys found in .env")

    return keys


class RoundRobinKeyManager:
    """Cycles through API keys to avoid rate limits"""

    def __init__(self):
        self.keys = get_api_keys()
        self._cycle = itertools.cycle(self.keys)
        print(f"Loaded {len(self.keys)} API key(s) for round robin")

    def get_next_key(self) -> str:
        return next(self._cycle)

    def __len__(self):
        return len(self.keys)


# Singleton instance
key_manager = RoundRobinKeyManager()