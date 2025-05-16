from flask import session
from misc import models, logging

def getRewards():
    """
    Get the rewards for a user
    """
    logging.log("Fetching all rewards...", "info")
    try:
        rewards = session.query(models.Reward).all()
        logging.log(f"Fetched {len(rewards)} rewards.", "info")
        return rewards
    except Exception as e:
        logging.log("Error getting rewards: " + str(e), "critical")
        return None

def addReward(rewardID, price, name, desc, issuer, imgURL):
    """
    Add a reward to a user
    """
    logging.log(f"Adding reward {rewardID}...", "info")
    try:
        reward = models.Reward(rewardId=rewardID, name=name, desc=desc, points=price, issuer=issuer, imgURL=imgURL)
        session.add(reward)
        session.commit()
        logging.log(f"Reward {rewardID} added successfully.", "info")
        return True
    except Exception as e:
        logging.log("Error adding reward: " + str(e), "critical")
        return False

def deleteReward(rewardID):
    """
    Delete a reward from a user
    """
    logging.log(f"Deleting reward {rewardID}...", "info")
    try:
        reward = session.query(models.Reward).filter(models.Reward.rewardId == rewardID).first()
        if reward:
            session.delete(reward)
            session.commit()
            logging.log(f"Reward {rewardID} deleted successfully.", "info")
            return True
        else:
            logging.log(f"Reward {rewardID} not found.", "warning")
            return False
    except Exception as e:
        logging.log("Error deleting reward: " + str(e), "critical")
        return False
    
def updateReward(rewardID, price, name, desc, issuer, imgURL):
    """
    Update a reward
    """
    logging.log(f"Updating reward {rewardID}...", "info")
    try:
        reward = session.query(models.Reward).filter(models.Reward.rewardId == rewardID).first()
        if reward:
            reward.points = price
            reward.name = name
            reward.desc = desc
            reward.issuer = issuer
            reward.imgURL = imgURL
            session.commit()
            logging.log(f"Reward {rewardID} updated successfully.", "info")
            return True
        else:
            logging.log(f"Reward {rewardID} not found.", "warning")
            return False
    except Exception as e:
        logging.log("Error updating reward: " + str(e), "critical")
        return False
    
def getRewardById(rewardID):
    """
    Get a reward by its ID
    """
    logging.log(f"Fetching reward {rewardID}...", "info")
    try:
        reward = session.query(models.Reward).filter(models.Reward.rewardId == rewardID).first()
        if reward:
            logging.log(f"Reward {rewardID} fetched successfully.", "info")
        else:
            logging.log(f"Reward {rewardID} not found.", "warning")
        return reward
    except Exception as e:
        logging.log("Error getting reward: " + str(e), "critical")
        return None