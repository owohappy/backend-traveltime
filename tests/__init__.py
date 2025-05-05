from fastapi import Depends
import main
from misc import models, schemas
userID = 123456789
userEMAIL = "test@example.com"
hashed_password = main.hash_password("ExamplePassword1!")
password = "ExamplePassword1!"
token = ""

### -- Test API Call functions --- ###
assert main.register(models.user(id=userID, email=userEMAIL, hashed_password=main.hash_password("ExamplePassword1!"), email_verified=False),
Depends(main.get_session) 
)
token = main.login(schemas.UserLogin(email=userEMAIL, password=password) ,Depends(main.get_session) )
print("token generated: " + token)

