from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from auth.accountManagment import get_current_user
from misc import schemas, models, db
import gambling

app = APIRouter(tags=["Gambling"])

@app.post("/gamble/blackjack/startgame",
            response_model=schemas.GambleGame,
            status_code=status.HTTP_201_CREATED,
            summary="Start a new blackjack game",
            description="Creates a new blackjack game and returns the game ID")
async def start_game(
    game: schemas.GambleGameCreate,
    session: Session = Depends(db.get_session),
    current_user: models.User = Depends(get_current_user)
):
    """Start a new blackjack game"""
    return await gambling.start_game(game, session, current_user)

