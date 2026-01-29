"""
Whale Trade History Collector for ML Training

Downloads complete trade history from profitable whale wallets on Hyperliquid.
This data can be used to train ML models to recognize winning patterns.

API Limits:
- Max 2000 fills per request
- Only 10000 most recent fills available per wallet
- Pagination via time-based cursoring
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests

from src.alpha_signals import KNOWN_WHALE_ADDRESSES

logger = logging.getLogger(__name__)

# Hyperliquid API endpoint
HL_INFO_URL = "https://api.hyperliquid.xyz/info"

# Data storage
DATA_DIR = Path("data/whale_trades")


class WhaleDataCollector:
    """Collects and stores whale trade history for ML training."""
    
    def __init__(self, whale_addresses: List[Dict] = None):
        """Initialize with list of whale addresses to track.
        
        Args:
            whale_addresses: List of dicts with 'address', 'name', 'reason' keys.
                           Defaults to KNOWN_WHALE_ADDRESSES.
        """
        self.whales = whale_addresses or KNOWN_WHALE_ADDRESSES
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Create data directory
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        
    def get_fills_by_time(
        self, 
        address: str, 
        start_time_ms: int,
        end_time_ms: int = None,
        aggregate: bool = True
    ) -> List[Dict]:
        """Fetch fills for an address within a time range.
        
        Args:
            address: Wallet address (0x...)
            start_time_ms: Start time in milliseconds
            end_time_ms: End time in milliseconds (default: now)
            aggregate: Combine partial fills
            
        Returns:
            List of fill objects
        """
        payload = {
            "type": "userFillsByTime",
            "user": address,
            "startTime": start_time_ms,
            "aggregateByTime": aggregate
        }
        if end_time_ms:
            payload["endTime"] = end_time_ms
            
        try:
            response = self.session.post(HL_INFO_URL, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch fills for {address[:10]}...: {e}")
            return []
    
    def download_whale_history(
        self, 
        address: str, 
        name: str = "",
        days_back: int = 90
    ) -> Dict[str, Any]:
        """Download complete trade history for a whale.
        
        Uses pagination to get up to 10000 most recent fills.
        
        Args:
            address: Wallet address
            name: Human-readable name
            days_back: How far back to fetch (max ~90 days usually)
            
        Returns:
            Dict with whale info and all fills
        """
        logger.info(f"🐋 Downloading history for {name or address[:10]}...")
        
        all_fills = []
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = int((datetime.now() - timedelta(days=days_back)).timestamp() * 1000)
        
        # Paginate through fills (max 2000 per request)
        current_end = end_time
        max_iterations = 10  # Safety limit (10 * 2000 = 20000 fills max)
        
        for i in range(max_iterations):
            fills = self.get_fills_by_time(address, start_time, current_end)
            
            if not fills:
                break
                
            all_fills.extend(fills)
            logger.info(f"   Fetched {len(fills)} fills (total: {len(all_fills)})")
            
            # Check if we got less than 2000 (means no more data)
            if len(fills) < 2000:
                break
                
            # Move cursor to oldest fill time - 1ms
            oldest_time = min(f.get("time", current_end) for f in fills)
            current_end = oldest_time - 1
            
            if current_end <= start_time:
                break
        
        return {
            "address": address,
            "name": name,
            "download_time": datetime.now().isoformat(),
            "total_fills": len(all_fills),
            "fills": all_fills
        }
    
    def download_all_whales(self, days_back: int = 90) -> Dict[str, Any]:
        """Download trade history for all tracked whales.
        
        Returns:
            Dict with summary and per-whale data
        """
        logger.info(f"🐋 Starting whale data collection for {len(self.whales)} wallets...")
        
        results = {
            "collection_time": datetime.now().isoformat(),
            "whales_tracked": len(self.whales),
            "total_fills": 0,
            "whale_data": {}
        }
        
        for whale in self.whales:
            address = whale["address"]
            name = whale.get("name", f"Whale_{address[:8]}")
            
            data = self.download_whale_history(address, name, days_back)
            results["whale_data"][address] = data
            results["total_fills"] += data["total_fills"]
            
            # Save individual whale data
            whale_file = DATA_DIR / f"{name}_{address[:8]}.json"
            with open(whale_file, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(f"   💾 Saved to {whale_file}")
        
        # Save combined summary
        summary_file = DATA_DIR / "whale_summary.json"
        with open(summary_file, "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"✅ Downloaded {results['total_fills']} fills from {len(self.whales)} whales")
        return results

    def prepare_training_data(self) -> List[Dict]:
        """Convert whale fills into ML training features.

        Creates feature vectors from trade data:
        - Entry/exit timing patterns
        - Position sizing patterns
        - Asset preferences
        - Win/loss patterns

        Returns:
            List of training samples with features and labels
        """
        training_data = []

        # Load all whale data
        for json_file in DATA_DIR.glob("Whale_*.json"):
            with open(json_file) as f:
                whale_data = json.load(f)

            fills = whale_data.get("fills", [])
            if not fills:
                continue

            # Group fills by asset to analyze complete trades
            by_asset = {}
            for fill in fills:
                coin = fill.get("coin", "")
                if coin not in by_asset:
                    by_asset[coin] = []
                by_asset[coin].append(fill)

            # Analyze each asset's trades
            for coin, asset_fills in by_asset.items():
                # Sort by time
                asset_fills.sort(key=lambda x: x.get("time", 0))

                for fill in asset_fills:
                    # Create training sample
                    sample = {
                        # Features
                        "asset": coin,
                        "side": fill.get("side", ""),  # B=Buy, A=Sell
                        "direction": fill.get("dir", ""),  # Open Long, Close Short, etc
                        "size": float(fill.get("sz", 0)),
                        "price": float(fill.get("px", 0)),
                        "start_position": float(fill.get("startPosition", 0)),
                        "hour_of_day": datetime.fromtimestamp(fill.get("time", 0) / 1000).hour,
                        "day_of_week": datetime.fromtimestamp(fill.get("time", 0) / 1000).weekday(),

                        # Label (outcome)
                        "closed_pnl": float(fill.get("closedPnl", 0)),
                        "is_profitable": float(fill.get("closedPnl", 0)) > 0,

                        # Metadata
                        "whale_address": whale_data.get("address", ""),
                        "timestamp": fill.get("time", 0),
                    }
                    training_data.append(sample)

        logger.info(f"📊 Prepared {len(training_data)} training samples from whale trades")
        return training_data

    def analyze_whale_patterns(self) -> Dict[str, Any]:
        """Analyze winning patterns from whale trade data.

        Returns insights like:
        - Best times to trade
        - Preferred assets
        - Average position sizes
        - Win rates by asset/time
        """
        training_data = self.prepare_training_data()

        if not training_data:
            return {"error": "No training data available"}

        # Analyze patterns
        analysis = {
            "total_trades": len(training_data),
            "winning_trades": sum(1 for t in training_data if t["is_profitable"]),
            "by_asset": {},
            "by_hour": {h: {"wins": 0, "total": 0} for h in range(24)},
            "by_day": {d: {"wins": 0, "total": 0} for d in range(7)},
            "by_direction": {},
        }

        # Win rate
        analysis["win_rate"] = analysis["winning_trades"] / max(1, analysis["total_trades"])

        # By asset
        for trade in training_data:
            asset = trade["asset"]
            if asset not in analysis["by_asset"]:
                analysis["by_asset"][asset] = {"wins": 0, "total": 0, "pnl": 0}
            analysis["by_asset"][asset]["total"] += 1
            analysis["by_asset"][asset]["pnl"] += trade["closed_pnl"]
            if trade["is_profitable"]:
                analysis["by_asset"][asset]["wins"] += 1

            # By hour
            hour = trade["hour_of_day"]
            analysis["by_hour"][hour]["total"] += 1
            if trade["is_profitable"]:
                analysis["by_hour"][hour]["wins"] += 1

            # By day
            day = trade["day_of_week"]
            analysis["by_day"][day]["total"] += 1
            if trade["is_profitable"]:
                analysis["by_day"][day]["wins"] += 1

            # By direction
            direction = trade["direction"]
            if direction not in analysis["by_direction"]:
                analysis["by_direction"][direction] = {"wins": 0, "total": 0}
            analysis["by_direction"][direction]["total"] += 1
            if trade["is_profitable"]:
                analysis["by_direction"][direction]["wins"] += 1

        # Calculate win rates
        for asset_data in analysis["by_asset"].values():
            asset_data["win_rate"] = asset_data["wins"] / max(1, asset_data["total"])
        for hour_data in analysis["by_hour"].values():
            hour_data["win_rate"] = hour_data["wins"] / max(1, hour_data["total"])
        for day_data in analysis["by_day"].values():
            day_data["win_rate"] = day_data["wins"] / max(1, day_data["total"])
        for dir_data in analysis["by_direction"].values():
            dir_data["win_rate"] = dir_data["wins"] / max(1, dir_data["total"])

        # Best trading hours
        best_hours = sorted(
            analysis["by_hour"].items(),
            key=lambda x: x[1]["win_rate"],
            reverse=True
        )[:5]
        analysis["best_hours"] = [h[0] for h in best_hours if h[1]["total"] >= 10]

        # Best assets
        best_assets = sorted(
            analysis["by_asset"].items(),
            key=lambda x: x[1]["pnl"],
            reverse=True
        )[:10]
        analysis["best_assets"] = [a[0] for a in best_assets]

        # Save analysis
        analysis_file = DATA_DIR / "whale_analysis.json"
        with open(analysis_file, "w") as f:
            json.dump(analysis, f, indent=2)

        logger.info(f"📊 Whale pattern analysis complete:")
        logger.info(f"   Win rate: {analysis['win_rate']:.1%}")
        logger.info(f"   Best hours (UTC): {analysis['best_hours']}")
        logger.info(f"   Best assets: {analysis['best_assets'][:5]}")

        return analysis


# CLI interface
if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    parser = argparse.ArgumentParser(description="Collect whale trade data for ML training")
    parser.add_argument("--download", action="store_true", help="Download whale trade history")
    parser.add_argument("--analyze", action="store_true", help="Analyze whale patterns")
    parser.add_argument("--days", type=int, default=90, help="Days of history to fetch")

    args = parser.parse_args()

    collector = WhaleDataCollector()

    if args.download:
        collector.download_all_whales(days_back=args.days)

    if args.analyze:
        analysis = collector.analyze_whale_patterns()
        print(json.dumps(analysis, indent=2))

