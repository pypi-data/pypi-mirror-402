from enum import Enum

class TokenRotationStrategy(Enum):
    ROUND_ROBIN = "round_robin"
    LRU = "lru"
    STICKY = "sticky"

class OpenAI:
    def __init__(self, strategy=None):
        raise RuntimeError("A-ha! This is not a real project. Visit https://preownedgpt.com#reveal")

class TokenPool:
    def __init__(self):
        raise RuntimeError("A-ha! This is not a real project. Visit https://preownedgpt.com#reveal")

    def get_next(self): pass
    def get_stats(self): pass
