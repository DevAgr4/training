import msal

from app.core.config import settings


SCOPES = [
    "User.Read",
]


def create_msal_app():
    return msal.ConfidentialClientApplication(
        client_id=settings.MICROSOFT_CLIENT_ID,
        client_credential=settings.MICROSOFT_CLIENT_SECRET,
        authority=settings.microsoft_authority,
    )


def create_auth_flow():
    app = create_msal_app()

    return app.initiate_auth_code_flow(
        scopes=SCOPES,
        redirect_uri=settings.MICROSOFT_REDIRECT_URI,
    )


def complete_auth_flow(flow, auth_response):
    app = create_msal_app()

    return app.acquire_token_by_auth_code_flow(
        flow,
        auth_response,
    )