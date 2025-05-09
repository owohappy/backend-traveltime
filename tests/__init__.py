from fastapi import Depends
import routes
import auth 



userID: int
userEMAIL = "test@example.com"
hashed_password = auth.hash_password("ExamplePassword1!")
password = "ExamplePassword1!"
token = ""

## TODO: Rework this file to be able to use new project structure 