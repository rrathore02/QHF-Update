# Clears the local user cache, effectively logging the user out

import os

def logout_user():
    cache_path = os.path.join(os.path.dirname(__file__), '.user_cache.json')
    if os.path.exists(cache_path):
        os.remove(cache_path)  # Remove cache file to log out
        print("✅ You have been logged out.")
    else:
        print("⚠️ No user is currently logged in.")
