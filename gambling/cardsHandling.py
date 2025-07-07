import hashlib
import base64
import random

# Mapping card values to their names for display purposes
cardsMap = {
    1: "Ace",
    2: 2,
    3: 3,
    4: 4,
    5: 5,
    6: 6,   
    7: 7,
    8: 8,
    9: 9,
    10: 10,
    11: "Jack",
    12: "Queen",
    13: "King"
}

# Game constants
WINNING_AMOUNT = 21
DEALER_STAND = 17
PAYOUT_ON_BJ = 2.5
PAYOUT_ON_WIN = 2

def hash_seed(seed):
    # basic seed hashing for fair gambling
    seed_str = str(seed).encode('utf-8')
    hash_object = hashlib.sha256(seed_str)
    base64_hash = base64.b64encode(hash_object.digest()).decode('utf-8')
    return base64_hash[:16]

def get_random_card(seed):
    # deterministic card generation based on seed
    random.seed(seed)
    return random.randint(1, 13)

def calculate_hand_value(cards):
    # ace handling for blackjack
    total = 0
    aces = 0
    for card in cards:
        if card == 1:
            aces += 1
            total += 11
        elif card >= 10:
            total += 10  # face cards
        else:
            total += card
    
    # adjust aces from 11 to 1 if needed
    while total > WINNING_AMOUNT and aces > 0:
        total -= 10
        aces -= 1
    return total

def get_card_name(card):
    return cardsMap.get(card, "Unknown")

def is_bust(cards):
    return calculate_hand_value(cards) > WINNING_AMOUNT

def is_blackjack(cards):
    return len(cards) == 2 and calculate_hand_value(cards) == WINNING_AMOUNT

def is_blackjack(cards):
    """
    Returns True if the hand is a blackjack (two cards totaling 21).
    """
    return len(cards) == 2 and calculate_hand_value(cards) == WINNING_AMOUNT

def hit_card(cards, seed):
    # draw another card
    card = get_random_card(seed)
    cards.append(card)
    if is_bust(cards):
        return True
    return card
