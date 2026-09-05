from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, JSONResponse

from app.core.config import settings
from app.services.microsoft_auth import (
    create_auth_flow,
    complete_auth_flow,
)


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


@router.get("/microsoft/login")
async def microsoft_login(request: Request):

    flow = create_auth_flow()

    # Store OAuth flow in the user's session.
    request.session["auth_flow"] = flow

    authorization_url = flow["auth_uri"]

    return RedirectResponse(
        url=authorization_url
    )


@router.get("/microsoft/callback")
async def microsoft_callback(
    request: Request
):

    auth_response = dict(request.query_params)

    flow = request.session.get("auth_flow")

    if not flow:
        return JSONResponse(
            status_code=400,
            content={
                "error": "Authentication session expired."
            },
        )

    try:
        result = complete_auth_flow(
            flow,
            auth_response,
        )

    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={
                "error": "Microsoft authentication failed.",
                "details": str(e),
            },
        )

    if "error" in result:

        return JSONResponse(
            status_code=401,
            content={
                "error": result.get("error"),
                "description": result.get(
                    "error_description"
                ),
            },
        )

    user = result.get(
        "id_token_claims",
        {}
    )

    # Store authenticated user in session.
    request.session["user"] = {
        "id": user.get("oid"),
        "name": user.get("name"),
        "email": user.get(
            "preferred_username"
        ),
    }

    # Remove OAuth flow after successful login.
    request.session.pop(
        "auth_flow",
        None
    )

    return RedirectResponse(
        url=f"{settings.FRONTEND_URL}/dashboard"
    )


@router.get("/me")
async def get_current_user(
    request: Request
):

    user = request.session.get("user")

    if not user:
        return JSONResponse(
            status_code=401,
            content={
                "authenticated": False,
                "message": "Not logged in",
            },
        )

    return {
        "authenticated": True,
        "user": user,
    }


@router.post("/logout")
async def logout(
    request: Request
):

    request.session.clear()

    return {
        "message": "Successfully logged out"
    }