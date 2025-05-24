from misc import logging

# Assuming a simple in-memory user store for demonstration

#get users from db
def getUsers():
    """
    Retrieves all users from the system.
    """
    return users

users = getUsers()

def deleteUser(user_id):
    """
    Deletes a user from the system if their class is 2.
    """
    global users

    user_to_delete = None
    for user_in_list in users:
        if user_in_list["id"] == user_id and user_in_list.get("class") == 2: # type: ignore
            user_to_delete = user_in_list
            break  # Found the user, no need to continue iterating
    
    if user_to_delete:
        users.remove(user_to_delete)
        logging.log(message=f"User {user_id} deleted.", type="info")
        return True
    else:
        logging.log(message=f"User {user_id} not found or not class 2.", type="warning")
        return False

def updateUser(user_id, **kwargs):
    """
    Updates a user's information in the system if their class is 2.
    """
    for user in users:
        if user["id"] == user_id and user.get("class") == 2:
            user.update(kwargs)
            logging.log(message=f"User {user_id} updated.", type="info")
            return True
    logging.log(message=f"User {user_id} not found or not class 2.", type="warning")
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
