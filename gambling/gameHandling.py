from gambling import cardsHandling
import random 
from flask import jsonify
import uuid
from misc import db, config
games = {}

def startGame(userID, betAmount):
    try:
        # Validate inputs
        if not isinstance(userID, str) or not isinstance(betAmount, (int, float)) or betAmount <= 0:
            return jsonify({"error": "Invalid input parameters"}), 400
            
        # Use parameterized queries and transaction management
        db.execute("BEGIN TRANSACTION") # type: ignore
        db.execute("SELECT * FROM users WHERE userID = ?", (userID,)) # type: ignore
        user = db.fetchone() # type: ignore
        
        if not user:
            db.execute("ROLLBACK") # type: ignore
            return jsonify({"error": "User not found"}), 404
            
        if user['points'] < betAmount:
            db.execute("ROLLBACK") # type: ignore
            return jsonify({"error": "Not enough points"}), 400
            
        db.execute("UPDATE users SET points = points - ? WHERE userID = ?", (betAmount, userID)) # type: ignore
        
        gameID = str(uuid.uuid4())
        seed = ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=48))
        hashedSeed = cardsHandling.hashSeed(seed) # type: ignore
        playerCard = [cardsHandling.getrandomCard(seed), cardsHandling.getrandomCard(seed)] # type: ignore
        dealerCard = [cardsHandling.getrandomCard(seed), cardsHandling.getrandomCard(seed)] # type: ignore

        if cardsHandling.checkBlackJack(playerCard): # type: ignore
            db.execute("UPDATE users SET points = points + ? WHERE userID = ?", (betAmount * cardsHandling.payoutOnBJ, userID)) # type: ignore
            db.execute("COMMIT") # type: ignore
            return jsonify({
                "gameID": gameID,
                "cards": {
                    "playerCards": playerCard,
                    "dealerCards": dealerCard
                },
                "seed": hashedSeed,
                "blackjack": True
            })
        
        if cardsHandling.checkBlackJack(dealerCard): # type: ignore
            db.execute("UPDATE users SET points = points + ? WHERE userID = ?", (betAmount * cardsHandling.payoutOnBJ, userID)) # type: ignore
            db.execute("COMMIT") # type: ignore
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

        db.execute("COMMIT") # type: ignore
        return jsonify({
            "gameID": gameID,
            "cards": {
                "playerCards": playerCard,
                "dealerCards": dealerCard[0]
            },
            "seed": hashedSeed
        })
    except Exception as e:
        db.execute("ROLLBACK") # type: ignore
        db.execute("UPDATE users SET points = points + ? WHERE userID = ?", (betAmount, userID)) # type: ignore
        db.commit() # type: ignore
        return jsonify({"error": str(e)}), 500
    

def continueGame(gameID: str, move: str):
    # Validate input
    if not isinstance(gameID, str) or not isinstance(move, str):
        return jsonify({"error": "Invalid input parameters"}), 400
    if gameID not in games:
        return jsonify({"error": "Game not found"}), 404
    if move not in ["hit", "stand"]:
        return jsonify({"error": "Invalid move"}), 400
    try:
        if move == "hit":
            # Implement hit logic
            pass
        elif move == "stand":
            # Implement stand logic
            pass
    except Exception as e:
        return jsonify({"error": str(e)}), 500