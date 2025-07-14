"""
Account Service

This microservice handles the lifecycle of Accounts
"""
# pylint: disable=unused-import
from flask import jsonify, request, make_response, abort, url_for   # noqa; F401
from service.models import Account
from service.common import status  # HTTP Status Codes
from . import app  # Import Flask application


############################################################
# Health Endpoint
############################################################
@app.route("/health")
def health():
    """Health Status"""
    return jsonify(dict(status="OK")), status.HTTP_200_OK


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Root URL response"""
    return (
        jsonify(
            name="Account REST API Service",
            version="1.0",
            paths=url_for("list_accounts", _external=True),  # Make sure this matches your function name
        ),
        status.HTTP_200_OK,
    )


######################################################################
# CREATE A NEW ACCOUNT
######################################################################
@app.route("/accounts", methods=["POST"])
def create_accounts():
    """
    Creates an Account
    This endpoint will create an Account based the data in the body that is posted
    """
    app.logger.info("Request to create an Account")
    check_content_type("application/json")
    account = Account()
    account.deserialize(request.get_json())
    account.create()
    message = account.serialize()
    # Uncomment once get_accounts has been implemented
    # location_url = url_for("get_accounts", account_id=account.id, _external=True)
    location_url = url_for("get_accounts", account_id=account.id, _external=True)
    return make_response(
        jsonify(message), status.HTTP_201_CREATED, {"Location": location_url}
    )

######################################################################
# LIST ALL ACCOUNTS
######################################################################
@app.route("/accounts", methods=["GET"])
def list_accounts():
    """
    Retrieve a list of Accounts
    This endpoint will return all Accounts unless a query parameter is specified
    """
    app.logger.info("Request for account list")
    
    accounts = Account.all()
    results = [account.serialize() for account in accounts]
    
    app.logger.info("Returning %d accounts", len(results))
    return jsonify(results), status.HTTP_200_OK 


######################################################################
# READ AN ACCOUNT
######################################################################
@app.route("/accounts/<int:account_id>", methods=["GET"])
def get_accounts(account_id):
    """
    Retrieve a single Account
    This endpoint will return an Account based on it's id
    """
    app.logger.info("Request for account with id: %s", account_id)
    
    # Find the account
    account = Account.find(account_id)
    if not account:
        abort(status.HTTP_404_NOT_FOUND, f"Account with id '{account_id}' was not found.")
    
    app.logger.info("Returning account: %s", account.name)
    return account.serialize(), status.HTTP_200_OK

######################################################################
# UPDATE AN EXISTING ACCOUNT
######################################################################

@app.route("/accounts/<int:account_id>", methods=["PUT"])
def update_accounts(account_id):
    """
    Update an Account
    This endpoint will update an Account based the body that is posted
    """
    app.logger.info("Request to update account with id: %s", account_id)
    check_content_type("application/json")
    
    # Find the account
    account = Account.find(account_id)
    if not account:
        abort(status.HTTP_404_NOT_FOUND, f"Account with id '{account_id}' was not found.")
    
    # Update the account with the new data
    account.deserialize(request.get_json())
    account.update()
    
    app.logger.info("Account with ID [%s] updated.", account.id)
    return account.serialize(), status.HTTP_200_OK


######################################################################
# DELETE AN ACCOUNT
######################################################################

@app.route("/accounts/<int:account_id>", methods=["DELETE"])
def delete_accounts(account_id):
    """
    Delete an Account
    This endpoint will delete an Account based the id specified in the path
    """
    app.logger.info("Request to delete account with id: %s", account_id)
    
    # Find the account
    account = Account.find(account_id)
    if account:
        account.delete()
        app.logger.info("Account with ID [%s] delete complete.", account_id)
    
    return "", status.HTTP_204_NO_CONTENT


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################


def check_content_type(media_type):
    """Checks that the media type is correct"""
    content_type = request.headers.get("Content-Type")
    if content_type and content_type == media_type:
        return
    app.logger.error("Invalid Content-Type: %s", content_type)
    abort(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        f"Content-Type must be {media_type}",
    )
