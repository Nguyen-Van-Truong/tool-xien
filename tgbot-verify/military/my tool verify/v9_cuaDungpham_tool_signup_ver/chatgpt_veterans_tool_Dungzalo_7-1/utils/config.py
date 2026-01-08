"""
Config - Lưu và load cấu hình
"""

import json
import os


class Config:
    """Config handler"""
    
    CONFIG_FILE = 'config.json'
    
    @staticmethod
    def save(config: dict):
        """Lưu config"""
        try:
            with open(Config.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {str(e)}")
    
    @staticmethod
    def load() -> dict:
        """Load config"""
        try:
            if os.path.exists(Config.CONFIG_FILE):
                with open(Config.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception as e:
            print(f"Error loading config: {str(e)}")
            return None

