import os
import requests
from keycloak import KeycloakOpenID

AUTHORIZER_API = os.environ["AUTHORIZER_API"]
KEYCLOAK_SERVER = f"{os.environ['KEYCLOAK_SERVER']}/auth/"
KEYCLOAK_REALM = os.environ["KEYCLOAK_REALM"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]


def webhook_token_is_authorized(webhook_token, dataset_id):
    client = KeycloakOpenID(
        server_url=KEYCLOAK_SERVER,
        realm_name=KEYCLOAK_REALM,
        client_id=os.environ["CLIENT_ID"],
        client_secret_key=CLIENT_SECRET,
    )
    response = client.token(grant_type=["client_credentials"])
    access_token = f"{response['token_type']} {response['access_token']}"

    authorize_response = requests.get(
        f"{AUTHORIZER_API}/{dataset_id}/webhook/{webhook_token}/authorize",
        headers={"Authorization": access_token},
    )

    authorize_response.raise_for_status()
    response_data = authorize_response.json()
    return response_data["access"], response_data.get("reason")
