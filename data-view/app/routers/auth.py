# app/routers/auth.py
import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.auth import (
    verify_password, create_access_token, create_refresh_token,
    decode_token, get_current_active_user
)
from app.models import Token, RefreshTokenRequest, UserPublic
from app.config import settings
from app.database import database # Direct access for user lookup

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate user with username and password (form data) and return JWT tokens.
    Uses standard OAuth2PasswordRequestForm for input.
    """
    logger.info(f"Login attempt for user: {form_data.username}")
    query = "SELECT id, username, hashed_password, is_active FROM users WHERE username = :username"
    user_dict = await database.fetch_one(query=query, values={"username": form_data.username})

    if not user_dict:
        logger.warning(f"Login failed: User '{form_data.username}' not found.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = user_dict # Directly use the dict for checks

    if not verify_password(form_data.password, user["hashed_password"]):
        logger.warning(f"Login failed: Invalid password for user '{form_data.username}'.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user["is_active"]:
         logger.warning(f"Login failed: User '{form_data.username}' is inactive.")
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")


    # Identity for the token subject (usually username or user ID)
    identity = {"sub": user["username"]}

    access_token = create_access_token(data=identity)
    refresh_token = create_refresh_token(data=identity)

    logger.info(f"Login successful for user: {form_data.username}")
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }

@router.post("/token/refresh", response_model=Token)
async def refresh_access_token(request: RefreshTokenRequest):
    """
    Refresh the access token using a valid refresh token.
    Returns a new access token and the original refresh token.
    """
    logger.info("Attempting to refresh access token.")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(request.refresh_token)
    if payload is None:
        logger.warning("Refresh token decoding failed or token expired.")
        raise credentials_exception

    # Check if it's a refresh token
    token_type = payload.get("type")
    if token_type != "refresh":
         logger.warning(f"Invalid token type provided for refresh: {token_type}")
         raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type, expected 'refresh'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username: Optional[str] = payload.get("sub")
    if username is None:
        logger.warning("Username ('sub') not found in refresh token payload.")
        raise credentials_exception

    # Optional: Verify the user still exists and is active in the database
    query = "SELECT id, is_active FROM users WHERE username = :username"
    user = await database.fetch_one(query=query, values={"username": username})
    if not user or not user["is_active"]:
        logger.warning(f"User '{username}' from refresh token not found or inactive in DB.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with refresh token is invalid or inactive",
        )

    # Create a new access token
    identity = {"sub": username}
    new_access_token = create_access_token(data=identity)

    logger.info(f"Access token refreshed successfully for user: {username}")
    # Return new access token and *original* refresh token
    # Or you could issue a new refresh token as well if desired
    return {
        "access_token": new_access_token,
        "refresh_token": request.refresh_token, # Or create_refresh_token(identity)
        "token_type": "bearer",
    }

@router.get("/users/me", response_model=UserPublic)
async def read_users_me(current_user: UserPublic = Depends(get_current_active_user)):
    """
    Get the profile of the currently authenticated user.
    """
    logger.debug(f"Fetching profile for user: {current_user.username}")
    # current_user already comes validated and as the correct Pydantic model
    # If get_current_active_user returned UserInDB, you'd convert it here.
    return current_user

# Note: As per request "直接使用sql语句添加账户" (directly use SQL to add accounts),
# an API endpoint for user *creation* is omitted here.
# Administration/user creation would happen via direct database access or a separate tool.
