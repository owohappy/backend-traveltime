from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from auth.accountManagment import get_current_user
from misc import schemas, models, db
import gambling

app = APIRouter(tags=["Gambling"])

@app.post("/gamble/blackjack/startgame",
            response_model=schemas.GambleGame, # type: ignore
            status_code=status.HTTP_201_CREATED,
            summary="Start a new blackjack game",
            description="Creates a new blackjack game and returns the game ID")
async def start_game(
    game: schemas.GambleGameCreate, # type: ignore
    session: Session = Depends(db.get_session),
    current_user: models.User = Depends(get_current_user)
):
    """Start a new blackjack game"""
    return await gambling.start_game(game, session, current_user) # type: ignore



@app.post("/gamble/blackjack/action",
            response_model=schemas.GambleGame, # type: ignore
            status_code=status.HTTP_200_OK,
            summary="Perform an action in a blackjack game",
            description="Performs an action in a blackjack game and returns the updated game state")
async def action(
    game: schemas.GambleGameAction, # type: ignore
    session: Session = Depends(db.get_session),
    current_user: models.User = Depends(get_current_user)
):
    """Perform an action in a blackjack game"""
    return await gambling.action(game, session, current_user) # type: ignore

