"""
Configuration and environment management for Operation Liquid Matrix v2.0
Centralized configuration with validation and type safety
"""
import os
from dataclasses import dataclass
from typing import Dict, List, Optional
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

@dataclass
class FirebaseConfig:
    """Firebase configuration with validation"""
    project_id: str
    service_account_key_path: str
    database_url: Optional[str] = None
    
    def __post_init__(self):
        if not os.path.exists(self.service_account_key_path):
            raise FileNotFoundError(
                f"Firebase service account key not found at: {self.service_account_account_key_path}"
            )

@dataclass
class WalletConfig:
    """Hot wallet configuration per chain"""
    chain: str
    addresses: List[str]
    max_daily_volume: float = 10000.0  # USD
    min_balance_alert: float = 100.0   # USD
    
@dataclass
class ExchangeConfig:
    """Exchange API configuration"""
    name: str
    api_key: str
    api_secret: str
    enable_rate_limit: bool = True
    timeout: int = 30000  # ms
    
@dataclass
class ExtractionConfig:
    """Profit extraction parameters"""
    min_profit_threshold: float = 0.015  # 1.5%
    max_profit_threshold: float = 0.04   # 4.0%
    base_extraction_percentage: float = 0.70  # 70%
    price_stability_period: int = 1800  # 30 minutes in seconds
    vault_wallet_address: str = ""  # To be set during initialization

class Config:
    """Main configuration manager"""
    
    def __init__(self):
        # Firebase
        self.firebase = FirebaseConfig(
            project_id=os.getenv("FIREBASE_PROJECT_ID", "liquid-matrix-v2"),
            service_account_key_path=os.getenv("FIREBASE_KEY_PATH", "./serviceAccountKey.json"),
            database_url=os.getenv("FIREBASE_DATABASE_URL")
        )
        
        # Exchanges
        self.exchanges: List[ExchangeConfig] = []
        self._load_exchange_configs()
        
        # Wallets
        self.wallets: List[WalletConfig] = [
            WalletConfig(chain="ethereum", addresses=os.getenv("ETH_WALLETS", "").split(",")),
            WalletConfig(chain="base", addresses=os.getenv("BASE_WALLETS", "").split(",")),
            WalletConfig(chain="arbitrum", addresses=os.getenv("ARB_WALLETS", "").split(","))
        ]
        
        # Extraction
        self.extraction = ExtractionConfig()
        
        # System
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.panic_oracle_emails = os.getenv("PANIC_ORACLE_EMAILS", "").split(",")
        
        # Validate critical configs
        self._validate()
    
    def _load_exchange_configs(self):
        """Load exchange configurations from environment"""
        exchanges_data = {
            "binance": ("BINANCE_API_KEY", "BINANCE_API_SECRET"),
            "coinbase": ("COINBASE_API_KEY", "COINBASE_API_SECRET"),
            "kraken": ("KRAKEN_API_KEY", "KRAKEN_API_SECRET")
        }
        
        for name, (key_env, secret_env) in exchanges_data.items():
            api_key = os.getenv(key_env)
            api_secret = os.getenv(secret_env)
            
            if api_key and api_secret:
                self.exchanges.append(ExchangeConfig(
                    name=name,
                    api_key=api_key,
                    api_secret=api_secret
                ))
    
    def _validate(self):
        """Validate critical configuration"""
        if not self.exchanges:
            logging.warning("No exchange API keys configured")
        
        if not self.telegram_bot_token or not self.telegram_chat_id:
            logging.warning("Telegram notifications disabled - missing bot token or chat ID")
        
        if len(self.panic_oracle_emails) < 3:
            logging.warning("Less than 3 panic oracle emails configured")

# Global configuration instance
config = Config()