from misc import models, logging, db


def calcXP(user_id, minutes, session=None):
    """
    Calculate the XP for a user
    """
    logging.log(f"Calculating XP for user {user_id}...", "info")
    
    # Get a session if not provided
    close_session = False
    if not session:
        from misc import db
        session = db.get_session()
        close_session = True
        
    try:
        # Fetch the user from the database
        user = session.exec(select(models.User).where(models.User.id == int(user_id))).first()
        if not user:
            logging.log(f"User {user_id} not found.", "warning")
            return False
        
        # Calculate and apply the XP
        xp_to_add = int(minutes)
        user.xp += xp_to_add
        
        # Update the level if needed
        new_level = calculate_level(user.xp)
        if new_level > user.level:
            user.level = new_level
            logging.log(f"User {user_id} leveled up to {new_level}!", "info")
        
        # Commit the changes
        session.add(user)
        session.commit()
        
        logging.log(f"Added {xp_to_add} XP to user {user_id}", "info")
        return True
        
    except Exception as e:
        session.rollback()
        logging.log(f"Error calculating XP: {str(e)}", "error")
        return False
    finally:
        if close_session:
            session.close()
            
def calculate_level(xp):
    """Calculate level from XP using a logarithmic formula"""
    import math
    return max(1, int(math.log(xp + 100, 1.5)))