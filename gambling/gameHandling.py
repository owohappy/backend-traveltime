from gambling import cardsHandling
import random
from flask import jsonify
import uuid
from misc import db, config

games = {}

def startGame(userID, betAmount):
    try:
        db.execute("SELECT * FROM users WHERE userID = ?", (userID,))
        user = db.fetchone()
        if not user:
            return jsonify({"error": "User not found"}), 404
        if user['points'] < betAmount:
            return jsonify({"error": "Not enough points"}), 400

        db.execute("UPDATE users SET points = points - ? WHERE userID = ?", (betAmount, userID))
        db.commit()

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
            "hashedSeed": hashedSeed,
            "betAmount": betAmount
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
        # Attempt to refund bet if possible
        try:
            db.execute("UPDATE users SET points = points + ? WHERE userID = ?", (betAmount, userID))
            db.commit()
        except Exception:
            pass
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

def continueGame(gameID: str, move: str):
    try:
        if move not in ["hit", "stand"]:
            return jsonify({"error": "Invalid move"}), 400
        if gameID not in games:
            return jsonify({"error": "Game not found"}), 404

        game = games[gameID]
        userID = game["userID"]
        playerCards = game["playerCards"]
        dealerCards = game["dealerCards"]
        seed = game["seed"]
        betAmount = game.get("betAmount", config.minBet)

        if move == "hit":
            playerCards.append(cardsHandling.getrandomCard(seed))
            if cardsHandling.checkBlackJack(playerCards):
                db.execute("UPDATE users SET points = points + ? WHERE userID = ?", (betAmount * cardsHandling.payoutOnBJ, userID))
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
                db.execute("UPDATE users SET points = points - ? WHERE userID = ?", (betAmount, userID))
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
            playerValue = cardsHandling.getHandValue(playerCards)
            dealerValue = cardsHandling.getHandValue(dealerCards)
            if cardsHandling.checkBust(dealerCards):
                db.execute("UPDATE users SET points = points + ? WHERE userID = ?", (betAmount * cardsHandling.payoutOnWin, userID))
                db.commit()
                return jsonify({
                    "gameID": gameID,
                    "cards": {
                        "playerCards": playerCards,
                        "dealerCards": dealerCards
                    },
                    "win": True
                })
            elif dealerValue > playerValue:
                db.execute("UPDATE users SET points = points - ? WHERE userID = ?", (betAmount, userID))
                db.commit()
                return jsonify({
                    "gameID": gameID,
                    "cards": {
                        "playerCards": playerCards,
                        "dealerCards": dealerCards
                    },
                    "lose": True
                })
            elif dealerValue == playerValue:
                db.execute("UPDATE users SET points = points + ? WHERE userID = ?", (betAmount, userID))
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
                db.execute("UPDATE users SET points = points + ? WHERE userID = ?", (betAmount * cardsHandling.payoutOnWin, userID))
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
    except Exception as e:
        return jsonify({"error": "Internal server error", "details": str(e)}), 500