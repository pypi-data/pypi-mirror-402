"""
Whale ML Daily Retraining Scheduler

Automatically downloads new whale trade data and retrains the model daily.
Can be run as a standalone service or integrated into the trading bot.
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class WhaleMLScheduler:
    """Schedules automatic whale data collection and model retraining."""
    
    def __init__(
        self,
        retrain_hour_utc: int = 0,  # Retrain at midnight UTC
        download_days: int = 90,
        min_hours_between_retrains: int = 20,
    ):
        """Initialize scheduler.
        
        Args:
            retrain_hour_utc: Hour of day (UTC) to run retraining
            download_days: Days of whale history to download
            min_hours_between_retrains: Minimum hours between retrains
        """
        self.retrain_hour_utc = retrain_hour_utc
        self.download_days = download_days
        self.min_hours_between_retrains = min_hours_between_retrains
        
        self.last_retrain: Optional[datetime] = None
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        
        # Load last retrain time from file
        self._load_state()
    
    def _load_state(self):
        """Load scheduler state from file."""
        state_file = Path("data/whale_scheduler_state.txt")
        if state_file.exists():
            try:
                timestamp_str = state_file.read_text().strip()
                self.last_retrain = datetime.fromisoformat(timestamp_str)
                logger.info(f"🐋 Last whale ML retrain: {self.last_retrain}")
            except Exception as e:
                logger.warning(f"Failed to load scheduler state: {e}")
    
    def _save_state(self):
        """Save scheduler state to file."""
        state_file = Path("data/whale_scheduler_state.txt")
        state_file.parent.mkdir(parents=True, exist_ok=True)
        if self.last_retrain:
            state_file.write_text(self.last_retrain.isoformat())
    
    def should_retrain(self) -> bool:
        """Check if it's time to retrain."""
        now = datetime.utcnow()
        
        # Check if we're at the right hour
        if now.hour != self.retrain_hour_utc:
            return False
        
        # Check minimum time since last retrain
        if self.last_retrain:
            hours_since = (now - self.last_retrain).total_seconds() / 3600
            if hours_since < self.min_hours_between_retrains:
                return False
        
        return True
    
    async def run_retrain(self) -> dict:
        """Download whale data and retrain model.
        
        Returns:
            Dict with retrain results
        """
        logger.info("🐋 Starting scheduled whale ML retrain...")
        
        try:
            # Import here to avoid circular imports
            from src.whale_data_collector import WhaleDataCollector
            from src.whale_ml_model import WhalePatternModel
            
            # Step 1: Download latest whale data
            logger.info("🐋 Step 1/2: Downloading whale trade history...")
            collector = WhaleDataCollector()
            download_result = collector.download_all_whales(days_back=self.download_days)
            
            # Step 2: Train model
            logger.info("🐋 Step 2/2: Training whale pattern model...")
            model = WhalePatternModel()
            train_result = model.train()
            model.save()
            
            # Update state
            self.last_retrain = datetime.utcnow()
            self._save_state()
            
            logger.info(f"✅ Whale ML retrain complete!")
            logger.info(f"   Downloaded: {download_result.get('total_fills', 0)} fills")
            logger.info(f"   Accuracy: {train_result.get('val_accuracy', 0):.1%}")
            
            return {
                "status": "success",
                "timestamp": self.last_retrain.isoformat(),
                "fills_downloaded": download_result.get("total_fills", 0),
                "train_accuracy": train_result.get("val_accuracy", 0),
                "train_auc": train_result.get("val_auc", 0),
            }
            
        except Exception as e:
            logger.error(f"❌ Whale ML retrain failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def start(self):
        """Start the scheduler loop."""
        if self.is_running:
            logger.warning("Whale ML scheduler already running")
            return
        
        self.is_running = True
        logger.info(f"🐋 Whale ML scheduler started (retrain at {self.retrain_hour_utc}:00 UTC)")
        
        while self.is_running:
            try:
                if self.should_retrain():
                    await self.run_retrain()
                
                # Check every 30 minutes
                await asyncio.sleep(1800)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Whale ML scheduler error: {e}")
                await asyncio.sleep(60)
        
        logger.info("🐋 Whale ML scheduler stopped")
    
    def stop(self):
        """Stop the scheduler."""
        self.is_running = False
        if self._task:
            self._task.cancel()


# Singleton for easy access
_scheduler: Optional[WhaleMLScheduler] = None

def get_scheduler() -> WhaleMLScheduler:
    """Get or create the whale ML scheduler singleton."""
    global _scheduler
    if _scheduler is None:
        _scheduler = WhaleMLScheduler()
    return _scheduler

