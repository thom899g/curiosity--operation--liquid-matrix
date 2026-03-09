"""
Firebase initialization and Firestore schema setup for Operation Liquid Matrix v2.0
Primary state management system with graceful degradation
"""
import firebase_admin
from firebase_admin import credentials, firestore, initialize_app
from google.cloud.firestore_v1.base_client import BaseClient
from typing import Optional, Dict, Any
import logging
from datetime import datetime

from config import config
from logger import get_logger

# Initialize logger
logger = get_logger("firebase_setup")

class FirebaseManager:
    """Manages Firebase connection and Firestore schema"""
    
    _instance: Optional['FirebaseManager'] = None
    _db: Optional[BaseClient] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self._initialize_firebase()
            self._setup_schema()
    
    def _initialize_firebase(self):
        """Initialize Firebase connection with error handling"""
        try:
            # Check if already initialized
            if firebase_admin._apps:
                logger.info("Firebase already initialized")
                self._db = firestore.client()
                return
            
            # Initialize with service account
            cred = credentials.Certificate(config.firebase.service_account_key_path)
            
            app_options = {"projectId": config.firebase.project_id}
            if config.firebase.database_url:
                app_options["databaseURL"] = config.firebase.database_url
            
            app = initialize_app(cred, app_options)
            self._db = firestore.client(app)
            
            logger.info(f"Firebase initialized successfully for project: {config.firebase.project_id}")
            
        except FileNotFoundError as e:
            logger.critical(f"Firebase service account key not found: {str(e)}")
            raise
        except Exception as e:
            logger.critical(f"Failed to initialize Firebase: {str(e)}")
            # Continue without Firebase for graceful degradation
            self._db = None
    
    def _setup_schema(self):
        """Initialize Firestore collections with default structure"""
        if not self._db:
            logger.warning("Firebase not available, skipping schema setup")
            return
        
        try:
            # Define collections and their default documents
            collections = {
                "strategies": self._get_strategy_schema(),
                "system_logs": {},
                "positions": self._get_position_schema(),
                "extraction_events": {},
                "panic_events": {},
                "vault_balance": self._get_vault_schema(),
                "performance_metrics": self._get_metrics_schema()
            }
            
            # Create collections if they don't exist (Firestore creates on first write)
            for collection_name, default_doc in collections.items():
                # Test write to ensure collection exists
                test_ref = self._db.collection(collection_name).document("_schema")
                if not test_ref.get().exists:
                    test_ref.set({
                        "created_at": datetime.utcnow().isoformat(),
                        "version": "2.0",
                        "defaults": default_doc
                    })
            
            logger.info("Firestore schema initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup Firestore schema: {str(e)}")
    
    def _get_strategy_schema(self) -> Dict[str, Any]:
        """Return default strategy document structure"""
        return {
            "name": "",
            "risk_adjusted_score": 0.0,
            "extraction_efficiency_30d": 0.0,
            "capital_allocated": 0.0,
            "last_updated": "",
            "is_active": False,
            "performance_signature": {},
            "created_at": "",
            "profit_target": 0.02,
            "max_drawdown": 0.05,
            "execution_count": 0,
            "success_count": 0
        }
    
    def _get_position_schema(self) -> Dict[str, Any]:
        """Return default position document structure"""
        return {
            "symbol": "",
            "entry_price": 0.0,
            "current_price": 0.0,
            "quantity": 0.0,
            "entry_time": "",
            "strategy_id": "",
            "status": "open",  # open, closed, extracted
            "profit_percentage": 0.0,
            "extraction_triggered": False,
            "wallet_address": "",
            "exchange": ""
        }
    
    def _get_vault_schema(self) -> Dict[str, Any]:
        """Return default vault balance document structure"""
        return {
            "total_balance": 0.0,
            "hardware_reserve": 0.0,
            "yield_engine_balance": 0.0,
            "trading_capital": 0.0,
            "last_rebalance": "",
            "monthly_hardware_target": 2000.0,
            "extraction_efficiency": 0.0,
            "updated_at": ""
        }
    
    def _get_metrics_schema(self) -> Dict[str, Any]:
        """Return default metrics document structure"""
        return {
            "capital_velocity": 0.0,
            "extraction_stealth": 0.0,
            "strategy_darwinism": 0,
            "yield_amplification": 0.0,
            "system_uptime": 100.0,
            "regulatory_opacity": 0,
            "calculated_at": ""
        }
    
    @property
    def db(self) -> Optional[BaseClient]:
        """Get Firestore database client with null check"""
        return self._db
    
    def is_connected(self) -> bool:
        """Check if Firebase is connected"""
        return self._db is not None
    
    def test_connection(self) -> bool:
        """Test Firebase connection"""
        if not self._db:
            return False
        
        try:
            # Simple read operation to test connection
            test_ref = self._db.collection("_connection_test").document("test")
            test_ref.set({"test": True, "timestamp": datetime.utcnow().isoformat()})
            test_ref.delete()
            return True
        except Exception as e:
            logger.error(f"Firebase connection test failed: {str(e)}")
            return False

# Global Firebase manager instance
firebase_manager = FirebaseManager()