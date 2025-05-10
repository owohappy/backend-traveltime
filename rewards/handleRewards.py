from misc import logging, models




def getRewards(session, rewardId):
    """
    Get the rewards for a user
    """
    try:
        rewards = session.query(models.Reward).filter(models.Reward.rewardId == rewardId).all()
        return rewards
    except Exception as e:
        logging.log("Error getting rewards: " + str(e), "critical")
        return None
    
    
def addReward(session, userId, rewardId, name, desc, points, issuer):
    """
    Add a reward to a user
    """
    try:
        reward = models.Reward(rewardId=rewardId, name=name, desc=desc, points=points, issuer=issuer)
        session.add(reward)
        session.commit()
        return True
    except Exception as e:
        logging.log("Error adding reward: " + str(e), "critical")
        return False
    
def deleteReward(session, userId, rewardId):
    """
    Delete a reward from a user
    """
    try:
        reward = session.query(models.Reward).filter(models.Reward.rewardId == rewardId).first()
        if reward:
            session.delete(reward)
            session.commit()
            return True
        else:
            return False
    except Exception as e:
        logging.log("Error deleting reward: " + str(e), "critical")
        return False
    
def updateReward(session, userId, rewardId, name, desc, points, issuer):   
    '''
    Update a reward
    '''
