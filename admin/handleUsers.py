from misc import logging

#TODO: WHOLE FILE IS A TODO
# Assuming a simple in-memory user store for demonstration
users = [
    {"id": 1, "username": "alice", "email": "alice@example.com", "phone": "1234567890", "class": 2},
    {"id": 2, "username": "bob", "email": "bob@example.com", "phone": "0987654321", "class": 1},
    # Add more users as needed
]

def deleteUser(user_id):
    """
    Deletes a user from the system if their class is 2.
    """
    global users
    for user in users:
        if user["id"] == user_id and user.get("class") == 2:
            users.remove(user)
            logging.info(f"User {user_id} deleted.")
            return True
    logging.warning(f"User {user_id} not found or not class 2.")
    return False

def updateUser(user_id, **kwargs):
    """
    Updates a user's information in the system if their class is 2.
    """
    for user in users:
        if user["id"] == user_id and user.get("class") == 2:
            user.update(kwargs)
            logging.info(f"User {user_id} updated.")
            return True
    logging.warning(f"User {user_id} not found or not class 2.")
    return False

def getUser(user_id):
    """
    Retrieves a user's information from the system if their class is 2.
    """
    for user in users:
        if user["id"] == user_id and user.get("class") == 2:
            return user
    return None

def getAllUsers():
    """
    Retrieves all users from the system with class 2.
    """
    return [user for user in users if user.get("class") == 2]

def getUserById(user_id):
    """
    Retrieves a user by their ID from the system if their class is 2.
    """
    return getUser(user_id)

def getUserByEmail(email):
    """
    Retrieves a user by their email from the system if their class is 2.
    """
    for user in users:
        if user["email"] == email and user.get("class") == 2:
            return user
    return None

def getUserByUsername(username):
    """
    Retrieves a user by their username from the system if their class is 2.
    """
    for user in users:
        if user["username"] == username and user.get("class") == 2:
            return user
    return None

def getUserByPhone(phone):
    """
    Retrieves a user by their phone number from the system if their class is 2.
    """
    for user in users:
        if user["phone"] == phone and user.get("class") == 2:
            return user
    return None
