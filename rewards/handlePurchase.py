

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

        # TODO: add logic to deliver the reward to the user

        return f"Purchase successful! You have bought {reward['name']}."
    else:
        return "Insufficient points to purchase this reward."
    
