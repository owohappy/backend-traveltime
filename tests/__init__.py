from fastapi import Depends
from routes import account, auth
from misc import db, models, schemas


userID: int
name: str
phonenumer: str
address: str
userEMAIL: str
hashed_password: str
password: str
token: str
name = "Ben Dover"
phonenumer = "1234567890"
address="123 Test St, Test City, TC 12345"
userEMAIL = "test@example.com"
hashed_password = auth.hash_password("ExamplePassword1!")
password = "ExamplePassword1!"
token = ""
userID = 0

## TODO: Rework this file to be able to use new project structure 

regresp = auth.register( 
schemas.UserCreate(
    email=userEMAIL,
    password=password,
    name=name,
    phonenumber=phonenumer,
    address=address
)
)

token = regresp["access_token"]
userID = regresp["userID"]

