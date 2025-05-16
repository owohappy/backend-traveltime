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
    """
    Hashes the given seed using SHA-256 and returns a base64-encoded string (first 16 chars).
    """
    seed_str = str(seed).encode('utf-8')
    hash_object = hashlib.sha256(seed_str)
    base64_hash = base64.b64encode(hash_object.digest()).decode('utf-8')
    return base64_hash[:16]

def get_random_card(seed):
    """
    Returns a pseudo-random card value (1-13) using the provided seed.
    """
    random.seed(seed)
    return random.randint(1, 13)

def calculate_hand_value(cards):
    """
    Calculates the total value of a hand, handling Aces as 1 or 11.
    """
    total = 0
    aces = 0
    for card in cards:
        if card == 1:
            aces += 1
            total += 11  # Initially treat Ace as 11
        elif card >= 10:
            total += 10  # Face cards are worth 10
        else:
            total += card
    # Adjust for Aces if total is over 21
    while total > WINNING_AMOUNT and aces > 0:
        total -= 10
        aces -= 1
    return total

def get_card_name(card):
    """
    Returns the display name of a card.
    """
    return cardsMap.get(card, "Unknown")

def is_bust(cards):
    """
    Returns True if the hand value exceeds 21.
    """
    return calculate_hand_value(cards) > WINNING_AMOUNT

def is_blackjack(cards):
    """
    Returns True if the hand is a blackjack (two cards totaling 21).
    """
    return len(cards) == 2 and calculate_hand_value(cards) == WINNING_AMOUNT

def hit_card(cards, seed):
    """
    Draws a card using the seed, adds it to the hand, and checks for bust.
    Returns True if bust, otherwise returns the drawn card.
    """
    card = get_random_card(seed)
    cards.append(card)
    if is_bust(cards):
        return True
    return card
