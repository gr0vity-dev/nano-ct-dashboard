import time


class CacheService:
    CACHE_TTL = 24 * 60 * 60  # Cache for a whole day

    def __init__(self):
        self.cache = {}

    def get_cache(self, key):
        cache_entry = self.cache.get(key)
        if cache_entry and time.time(
        ) - cache_entry['timestamp'] < cache_entry['ttl']:
            return cache_entry['value']

    def set_cache(self, key, value, ttl):
        self.cache[key] = {
            'value': value,
            'timestamp': time.time(),
            'ttl': ttl
        }
