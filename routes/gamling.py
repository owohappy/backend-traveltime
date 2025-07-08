from fastapi import APIRouter, Depends, status
from sqlmodel import Session
from auth.accountManagment import get_current_user
from misc import schemas, models, db
import gambling

app = APIRouter(tags=["Gambling"])

@app.post("/gamble/blackjack/start", status_code=status.HTTP_201_CREATED)
async def start_game(
    game: schemas.GambleGameCreate,
    session: Session = Depends(db.get_session),
    current_user: dict = Depends(get_current_user)
):
    return await gambling.start_game(game, session, current_user)

@app.post("/gamble/blackjack/action")
async def do_action(
    game: schemas.GambleGameAction,
    session: Session = Depends(db.get_session),
    current_user: dict = Depends(get_current_user)
):
    return await gambling.action(game, session, current_user)

