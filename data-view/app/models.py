# app/models.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

# --- Token Models ---
class Token(BaseModel):
    """
    Response model for successful login, containing tokens.
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """
    Data structure contained within the JWT payload (subject).
    """
    username: Optional[str] = None

class RefreshTokenRequest(BaseModel):
    """
    Request model for the token refresh endpoint.
    """
    refresh_token: str

# --- User Models ---
class UserBase(BaseModel):
    """
    Base user model with common fields.
    """
    username: str = Field(..., min_length=3, max_length=50)

class UserCreate(UserBase):
    """
    Model used for creating a new user (if an API endpoint is added).
    Requires password.
    """
    password: str = Field(..., min_length=6)

class UserInDBBase(UserBase):
    """
    Base model for user data stored in the database. Includes ID.
    """
    id: int
    is_active: bool = True

    class Config:
        # Allows model creation from ORM objects (like SQLAlchemy) or dicts
        from_attributes = True # For Pydantic V2
        # orm_mode = True # For Pydantic V1

class UserInDB(UserInDBBase):
    """
    Complete user data model as stored in DB, including hashed password.
    Should not be exposed directly via API responses without care.
    """
    hashed_password: str

class UserPublic(UserInDBBase):
    """
    User model suitable for public API responses (omits password).
    """
    pass # Inherits id, username, is_active

# --- Zookeeper Models ---
class ZookeeperNode(BaseModel):
    """
    Represents a node in Zookeeper with its path and data.
    """
    path: str
    data: Optional[str] = None # Data decoded as string (handle potential errors)
    error: Optional[str] = None # To report decoding errors

class ZookeeperChildren(BaseModel):
    """
    Represents a list of child node names for a given path.
    """
    path: str
    children: List[str]

class ZookeeperAllNodes(BaseModel):
    """
    Response model for getting all nodes (structure TBD - flat list or nested dict).
    Using a flat list of paths for simplicity here.
    """
    base_path: str
    all_paths: List[str]

class ZookeeperQueryRequest(BaseModel):
    """
    Request model for Zookeeper queries, specifying the path.
    """
    path: str = "/" # Default path if not provided
