#!/usr/bin/env python3
"""
Analytics Data Initialization Script
Populates the analytics system with sample data for testing and demonstration.
"""

import os
import sys
import json
import pickle
import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict
import random

# Add project root to path
sys.path.append('/workspaces/backend-traveltime')

# Import analytics modules
try:
    from travel import route_analytics, ANALYTICS_CACHE_FILE, TRANSPORT_PATTERNS_FILE
    print("✓ Analytics modules imported successfully")
except ImportError as e:
    print(f"✗ Failed to import analytics modules: {e}")
    sys.exit(1)

def create_sample_route_usage():
    """Create sample route usage data"""
    print("Creating sample route usage data...")
    
    # Sample route IDs (would come from actual routes in production)
    sample_routes = [
        "bus_route_123", "tram_route_456", "train_route_789",
        "bus_route_abc", "metro_route_def", "bus_route_xyz",
        "tram_route_ghi", "train_route_jkl", "bus_route_mno",
        "metro_route_pqr"
    ]
    
    # Generate usage statistics
    for route_id in sample_routes:
        usage_count = random.randint(5, 200)
        transport_type = route_id.split('_')[0]
        operator = f"{transport_type.title()} Transit Co."
        
        # Update analytics
        for _ in range(usage_count):
            route_analytics.update_route_usage(route_id, transport_type, operator)
    
    print(f"✓ Created usage data for {len(sample_routes)} routes")

def create_sample_transport_patterns():
    """Create sample transport pattern data"""
    print("Creating sample transport patterns...")
    
    # Sample transport types with characteristic patterns
    transport_patterns = {
        "bus": {
            "speeds": [15, 20, 25, 18, 22, 16, 19, 23, 17, 21],
            "stop_frequency": 0.8,
            "sample_count": 50
        },
        "tram": {
            "speeds": [25, 30, 35, 28, 32, 26, 31, 34, 27, 29],
            "stop_frequency": 0.6,
            "sample_count": 35
        },
        "train": {
            "speeds": [45, 55, 60, 50, 58, 48, 52, 62, 47, 54],
            "stop_frequency": 0.3,
            "sample_count": 75
        },
        "metro": {
            "speeds": [35, 40, 45, 38, 42, 36, 41, 44, 37, 39],
            "stop_frequency": 0.5,
            "sample_count": 40
        }
    }
    
    for transport_type, pattern_data in transport_patterns.items():
        # Learn patterns from sample data
        for i in range(pattern_data["sample_count"]):
            # Generate varying speed data
            speeds = [
                speed + random.uniform(-5, 5) 
                for speed in pattern_data["speeds"]
            ]
            
            route_analytics.learn_transport_pattern(
                transport_type,
                speeds,
                pattern_data["stop_frequency"] + random.uniform(-0.1, 0.1),
                f"sample_geometry_{transport_type}_{i}"
            )
    
    print(f"✓ Created patterns for {len(transport_patterns)} transport types")

def create_sample_analytics_cache():
    """Create sample analytics cache data"""
    print("Creating sample analytics cache...")
    
    # Sample route analytics
    sample_analytics = {}
    
    routes = [
        "bus_route_123", "tram_route_456", "train_route_789",
        "bus_route_abc", "metro_route_def", "bus_route_xyz"
    ]
    
    for route_id in routes:
        usage_count = random.randint(10, 150)
        last_used = datetime.now() - timedelta(hours=random.randint(1, 72))
        confidence = random.uniform(0.5, 0.95)
        
        sample_analytics[route_id] = {
            "usage_count": usage_count,
            "last_used": last_used.isoformat(),
            "confidence": confidence
        }
    
    # Save to cache
    route_analytics.analytics_cache = sample_analytics
    route_analytics._save_analytics_cache()
    
    print(f"✓ Created analytics cache for {len(sample_analytics)} routes")

def verify_analytics_data():
    """Verify the created analytics data"""
    print("\nVerifying analytics data...")
    
    # Check route usage
    total_usage = sum(route_analytics.route_usage_stats.values())
    print(f"✓ Total route usage events: {total_usage}")
    
    # Check popular routes
    popular_routes = route_analytics.get_popular_routes(5)
    print(f"✓ Popular routes: {len(popular_routes)}")
    
    if popular_routes:
        print(f"  Top route: {popular_routes[0][0]} ({popular_routes[0][1]} uses)")
    
    # Check operator stats
    operator_stats = route_analytics.get_operator_stats()
    print(f"✓ Operators tracked: {len(operator_stats)}")
    
    # Check transport patterns
    patterns = route_analytics.transport_patterns
    print(f"✓ Transport patterns: {len(patterns)}")
    
    for transport_type, pattern in patterns.items():
        print(f"  {transport_type}: {pattern.sample_count} samples, {pattern.confidence:.2f} confidence")

def main():
    """Initialize sample analytics data"""
    print("Analytics Data Initialization")
    print("=" * 50)
    
    try:
        # Create sample data
        create_sample_route_usage()
        create_sample_transport_patterns()
        create_sample_analytics_cache()
        
        # Verify data
        verify_analytics_data()
        
        print("\n" + "=" * 50)
        print("✓ Analytics data initialization completed successfully!")
        print("You can now test the analytics endpoints with sample data.")
        
    except Exception as e:
        print(f"\n✗ Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
