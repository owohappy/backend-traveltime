from flask import Blueprint

api = Blueprint('api', __name__)

@api.route('/ping', methods=['GET'])
def ping():
    """
    Health check endpoint.
    """
    return {"message": "Pong!"}, 200



