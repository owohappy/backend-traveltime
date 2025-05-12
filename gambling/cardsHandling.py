import hashlib
import base64
import random

cardsMap = {
1 : "Ace",
2 : 2,
3 : 3,
4 : 4,
5 : 5,
6 : 6,
7 : 7,
8 : 8,
9 : 9,
10 : 10,
11 : "Jack",
12 : "Queen",
13 : "King"
}

winingAmount = 21
dealerStand = 17
dealerHit = 16
payoutOnBJ = 2.5
payoutOnWin = 2

def hashSeed(seed):
    # Convert the seed to a string and encode it
    seed_str = str(seed).encode('utf-8')
    # Create a SHA-256 hash of the seed
    hash_object = hashlib.sha256(seed_str)
    # Convert the hash to a base64 string
    base64_hash = base64.b64encode(hash_object.digest()).decode('utf-8')
    # Return the first 16 characters of the base64 string
    return base64_hash[:16]

def getrandomCard(seed):
    random.seed(seed)
    return random.randint(1, 13)

def checkDealersHand(cardsDealer):
    #check how much the dealer has 
    return None