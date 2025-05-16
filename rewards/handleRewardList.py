

from flask import session
from misc import models, logging


def getRewards():
    """
    Get the rewards for a user
    """
    try:
        rewards = session.query(models.Reward).all()
        return rewards
    except Exception as e:
        logging.log("Error getting rewards: " + str(e), "critical")
        return None

def addReward(rewardID, price, name, desc, issuer, imgURL):
    """
    Add a reward to a user
    """
    try:
        reward = models.Reward(rewardId=rewardID, name=name, desc=desc, points=price, issuer=issuer, imgURL=imgURL)
        session.add(reward)
        session.commit()
        return True
    except Exception as e:
        logging.log("Error adding reward: " + str(e), "critical")
        return False

def deleteReward(rewardID):
    """
    Delete a reward from a user
    """
    try:
        reward = session.query(models.Reward).filter(models.Reward.rewardId == rewardID).first()
        if reward:
            session.delete(reward)
            session.commit()
            return True
        else:
            return False
    except Exception as e:
        logging.log("Error deleting reward: " + str(e), "critical")
        return False
    
def updateReward(rewardID, price, name, desc, issuer, imgURL):
    """
    Update a reward
    """
    try:
        reward = session.query(models.Reward).filter(models.Reward.rewardId == rewardID).first()
        if reward:
            reward.points = price
            reward.name = name
            reward.desc = desc
            reward.issuer = issuer
            reward.imgURL = imgURL
            session.commit()
            return True
        else:
            return False
    except Exception as e:
        logging.log("Error updating reward: " + str(e), "critical")
        return False
    
def getRewardById(rewardID):
    """
    Get a reward by its ID
    """
    try:
        reward = session.query(models.Reward).filter(models.Reward.rewardId == rewardID).first()
        return reward
    except Exception as e:
        logging.log("Error getting reward: " + str(e), "critical")
        return None