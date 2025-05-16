

def purchaseReward(reward, user):
    """
    Handles the purchase of a reward by a user.
    
    Args:
        reward (dict): The reward to be purchased.
        user (dict): The user purchasing the reward.
    
    Returns:
        str: A message indicating the result of the purchase.
    """
    if user['points'] >= reward['cost']:
        user['points'] -= reward['cost']

        try:
            # deduct points from user
            # add reward to user's inventory    
            return f"Purchase successful! You have bought {reward['name']}."
        except Exception as e:
            return f"Error processing purchase: {str(e)}"
    else:
        return "Insufficient points to purchase this reward."
    
