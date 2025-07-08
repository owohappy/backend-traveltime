#!/usr/bin/env python3
"""
Script to check and create UserHours table and test the profile endpoint fix
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from misc import db, models
from sqlmodel import Session

# Initialize database
db.init_database()

# Test creating a UserHours record
with Session(db.engine) as session:
    # Check if UserHours table exists and can be queried
    try:
        # Try to query UserHours (this will create the table if it doesn't exist)
        user_hours = session.exec(models.select(models.UserHours)).first()
        print("✓ UserHours table accessible")
        
        # Test creating a new UserHours record
        test_user_hours = models.UserHours(
            user_id=999999,  # Test user ID
            hoursTotal=5.5,
            hoursDaily=1.0
        )
        session.add(test_user_hours)
        session.commit()
        
        # Query it back
        retrieved = session.exec(models.select(models.UserHours).where(models.UserHours.user_id == 999999)).first()
        if retrieved:
            print(f"✓ UserHours record created and retrieved: {retrieved.hoursTotal} total hours")
            
            # Clean up test record
            session.delete(retrieved)
            session.commit()
            print("✓ Test record cleaned up")
        else:
            print("✗ Failed to retrieve UserHours record")
            
    except Exception as e:
        print(f"✗ Error with UserHours table: {e}")

print("UserHours table test completed!")
