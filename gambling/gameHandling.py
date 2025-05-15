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
        playerCard = [cardsHandling.getrandomCard(seed)]
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
        games[gameID] = {
            "userID": userID,
            "playerCards": playerCard,
            "dealerCards": dealerCard,
            "seed": seed,
            "hashedSeed": hashedSeed
        }
        return jsonify({
            "gameID": gameID,
            "cards": {
                "playerCards": playerCard,
                "dealerCards": dealerCard
            },
            "seed": hashedSeed
        })
    except Exception as e:
        db.execute("UPDATE users SET points = points + ? WHERE userID = ?", (config.minBet, userID))
        db.commit()
        return jsonify({"error": str(e)}), 500
    

def continueGame(gameID: int, move: str):
    if move not in ["hit", "stand"]:
        return jsonify({"error": "Invalid move"}), 400
    if gameID not in games:
        return jsonify({"error": "Game not found"}), 404
    game = games[gameID]
    userID = game["userID"]
    playerCards = game["playerCards"]
    dealerCards = game["dealerCards"]
    seed = game["seed"]

    if move == "hit":
        playerCards.append(cardsHandling.getrandomCard(seed))
        if cardsHandling.checkBlackJack(playerCards):
            db.execute("UPDATE users SET points = points + ? WHERE userID = ?", (config.minBet * cardsHandling.payoutOnBJ, userID))
            db.commit()
            return jsonify({
                "gameID": gameID,
                "cards": {
                    "playerCards": playerCards,
                    "dealerCards": dealerCards
                },
                "blackjack": True
            })
        elif cardsHandling.checkBust(playerCards):
            db.execute("UPDATE users SET points = points - ? WHERE userID = ?", (config.minBet, userID))
            db.commit()
            return jsonify({
                "gameID": gameID,
                "cards": {
                    "playerCards": playerCards,
                    "dealerCards": dealerCards
                },
                "bust": True
            })
        else:
            return jsonify({
                "gameID": gameID,
                "cards": {
                    "playerCards": playerCards,
                    "dealerCards": dealerCards
                }
            })
    elif move == "stand":
        while cardsHandling.getHandValue(dealerCards) < 17:
            dealerCards.append(cardsHandling.getrandomCard(seed))
        if cardsHandling.checkBust(dealerCards):
            db.execute("UPDATE users SET points = points + ? WHERE userID = ?", (config.minBet * cardsHandling.payoutOnWin, userID))
            db.commit()
            return jsonify({
                "gameID": gameID,
                "cards": {
                    "playerCards": playerCards,
                    "dealerCards": dealerCards
                },
                "win": True
            })
        elif cardsHandling.getHandValue(dealerCards) > cardsHandling.getHandValue(playerCards):
            db.execute("UPDATE users SET points = points - ? WHERE userID = ?", (config.minBet, userID))
            db.commit()
            return jsonify({
                "gameID": gameID,
                "cards": {
                    "playerCards": playerCards,
                    "dealerCards": dealerCards
                },
                "lose": True
            })
        elif cardsHandling.getHandValue(dealerCards) == cardsHandling.getHandValue(playerCards):
            db.execute("UPDATE users SET points = points + ? WHERE userID = ?", (config.minBet, userID))
            db.commit()
            return jsonify({
                "gameID": gameID,
                "cards": {
                    "playerCards": playerCards,
                    "dealerCards": dealerCards
                },
                "draw": True
            })
        else:
            db.execute("UPDATE users SET points = points + ? WHERE userID = ?", (config.minBet * cardsHandling.payoutOnWin, userID))
            db.commit()
            return jsonify({
                "gameID": gameID,
                "cards": {
                    "playerCards": playerCards,
                    "dealerCards": dealerCards
                },
                "win": True
            })
    else:
        return jsonify({"error": "Invalid move"}), 400
        
    