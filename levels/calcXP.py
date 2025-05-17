from misc import models, logging, db


def calcXP(userID, minutes):
    """
    Calculate the XP for a user
    """
    logging.log(f"Calculating XP for user {userID}...", "info")
    try:
        # Fetch the user from the database
        user = db.session.query(models.User).filter(models.User.userId == userID).first()
        if not user:
            logging.log(f"User {userID} not found.", "warning")
            return False

        # Calculate the XP based on the minutes spent

        # Check for multiplyers
        if user.xpMultiplier:
            minutes *= user.xpMultiplier
        else:
            user.xpMultiplier = 1
        # Check for level
        user.xp += minutes

        # Commit the changes to the database
        db.session.commit()
        logging.log(f"XP calculated and added for user {userID}.", "info")
        return True
    except Exception as e:
        logging.log("Error calculating XP: " + str(e), "critical")
        return False

def getLvl(userID):
    """
    Get the level of a user
    """
    logging.log(f"Getting level for user {userID}...", "info")
    try:
        # Fetch the user from the database
        user = db.session.query(models.User).filter(models.User.userId == userID).first()
        if not user:
            logging.log(f"User {userID} not found.", "warning")
            return False
        # Calculate the user's current level
        lvl = 1
        xp_needed = 10
        xp = user.xp

        while xp >= xp_needed:
            xp -= xp_needed
            lvl += 1
            xp_needed = int(xp_needed ** lvl)  # Increase XP needed for next level

        return {
            "level": lvl,
            "xp_current": xp,
            "xp_for_next_level": xp_needed
        }

    except Exception as e:
        logging.log("Error getting level: " + str(e), "critical")
        return False