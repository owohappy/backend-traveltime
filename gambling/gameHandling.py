from gambling import cardsHandling
import random 
from flask import jsonify
import uuid
from misc import db, config
games = {}

## TODO: make secure against sql injection

def startGame(userID, betAmount):
    db.execute("SELECT * FROM users WHERE userID = ?", (userID,))
    user = db.fetchone()
    if not user:
        return jsonify({"error": "User not found"}), 404
    if user['points'] < betAmount:
        return jsonify({"error": "Not enough points"}), 400
    else:
        db.execute("UPDATE users SET points = points - ? WHERE userID = ?", (betAmount, userID))
        db.commit()
    try:
        gameID = str(uuid.uuid4())
        seed = ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=48))
        hashedSeed = cardsHandling.hashSeed(seed)
        playerCard = [cardsHandling.getrandomCard(seed), cardsHandling.getrandomCard(seed)]
        dealerCard = [cardsHandling.getrandomCard(seed), cardsHandling.getrandomCard(seed)]

        if cardsHandling.checkBlackJack(playerCard):
            db.execute("UPDATE users SET points = points + ? WHERE userID = ?", (betAmount * cardsHandling.payoutOnBJ, userID))
            db.commit()
            return jsonify({
                "gameID": gameID,
                "cards": {
                    "playerCards": playerCard,
                    "dealerCards": dealerCard
                },
                "seed": hashedSeed,
                "blackjack": True
            })
        
        if cardsHandling.checkBlackJack(dealerCard):
            db.execute("UPDATE users SET points = points + ? WHERE userID = ?", (betAmount * cardsHandling.payoutOnBJ, userID))
            db.commit()
            return jsonify({
                "gameID": gameID,
                "cards": {
                    "playerCards": playerCard,
                    "dealerCards": dealerCard
                },
                "seed": hashedSeed,
                "blackjack": True
            })
        
        games[gameID] = {
            "userID": userID,
            "playerCards": playerCard,
            "dealerCards": dealerCard[0],
            "seed": seed,
            "hashedSeed": hashedSeed
        }



        return jsonify({
            "gameID": gameID,
            "cards": {
                "playerCards": playerCard,
                "dealerCards": dealerCard[0]
            },
            "seed": hashedSeed
        })
    except Exception as e:
        db.execute("UPDATE users SET points = points + ? WHERE userID = ?", (config.minBet, userID))
        db.commit()
        return jsonify({"error": str(e)}), 500
    

def continueGame(gameID: int, move: str):
    {
        
    }