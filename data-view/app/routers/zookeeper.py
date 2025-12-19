# app/routers/zookeeper.py
import logging
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

from fastapi import APIRouter, Depends, HTTPException, Query, Path as FastApiPath
from kazoo.client import KazooClient, NoNodeError
from kazoo.exceptions import KazooException

from app.config import settings
from app.auth import get_current_active_user
from app.models import UserPublic, ZookeeperNode, ZookeeperChildren, ZookeeperAllNodes

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/zookeeper", tags=["Zookeeper"])

# --- Zookeeper Client Management ---
# Global client instance (use with caution in production, consider connection pooling)
# A more robust approach might involve a dependency that manages the client lifecycle per request
# or a background task ensuring the connection is alive.
zk_client: Optional[KazooClient] = None

def get_zk_client() -> KazooClient:
    """
    Provides a connected KazooClient instance.
    Connects if not already connected. Handles basic connection state.
    Raises HTTPException if connection fails.
    """
    global zk_client
    try:
        if zk_client is None or not zk_client.connected:
            logger.info(f"Connecting to Zookeeper at {settings.ZOOKEEPER_HOSTS}")
            zk_client = KazooClient(hosts=settings.ZOOKEEPER_HOSTS, timeout=5.0) # Added timeout
            zk_client.start(timeout=10) # Wait up to 10 seconds for connection
            logger.info("Zookeeper connection established.")
        return zk_client
    except KazooException as e:
        logger.exception(f"Failed to connect or start Zookeeper client: {e}")
        zk_client = None # Reset client on failure
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not connect to Zookeeper: {e}"
        )
    except Exception as e: # Catch any other potential startup errors
         logger.exception(f"Unexpected error getting Zookeeper client: {e}")
         zk_client = None
         raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error connecting to Zookeeper: {e}"
         )


@contextmanager
def zk_connection():
    """
    Context manager for ensuring Zookeeper client is connected and handles cleanup.
    (Alternative to the global client approach)
    """
    client = None
    try:
        logger.debug("Attempting to get ZK client via context manager.")
        client = get_zk_client() # Reuse the connection logic
        yield client
    except HTTPException: # Propagate connection errors
        raise
    except KazooException as e:
        logger.error(f"Zookeeper operation failed: {e}")
        # Optionally try to reconnect or just raise
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Zookeeper error: {e}")
    # finally:
        # Decide on cleanup strategy:
        # - Keep connection open (if using global client mostly)
        # - Close connection per request (client.stop()) - less efficient
        # logger.debug("ZK Context manager exiting.")
        # pass # Assuming global client is managed elsewhere (e.g., startup/shutdown)


# --- Helper Function for Recursive Fetch ---
async def get_all_zk_nodes_recursive(client: KazooClient, path: str, all_paths: List[str]):
    """
    Recursively fetches all node paths starting from the given path.
    Appends full paths to the `all_paths` list.
    Handles NoNodeError gracefully for paths that might disappear.
    """
    try:
        children = await client.get_children_async(path)
        # Add current path only if it's not the root (or if root is desired)
        # if path != '/': # Optional: exclude root itself unless specifically requested
        #    all_paths.append(path) # Decided to include all valid paths found

        for child in children:
            # Construct the full path for the child
            child_path = f"{path}/{child}" if path != "/" else f"/{child}"
            all_paths.append(child_path) # Add child path
            # Recursively explore the child path
            await get_all_zk_nodes_recursive(client, child_path, all_paths)

    except NoNodeError:
        logger.warning(f"Node not found during recursive scan: {path}")
        # Node might have been deleted between get_children and recursive call, just stop for this branch
    except KazooException as e:
        logger.error(f"Error getting children or recursing for path {path}: {e}")
        # Decide whether to stop or continue with other branches
        # For now, log and stop recursion down this specific path
    except Exception as e:
        logger.exception(f"Unexpected error during recursive ZK scan at {path}: {e}")


# --- API Endpoints ---

@router.get("/keys", response_model=ZookeeperAllNodes)
async def get_all_zookeeper_keys(
    path: str = Query("/", description="Base path to start scanning from."),
    current_user: UserPublic = Depends(get_current_active_user) # Require authentication
):
    """
    Retrieves all Zookeeper node paths recursively starting from the specified base path.
    Requires authentication.
    """
    logger.info(f"User '{current_user.username}' requested all ZK keys starting from path: {path}")
    all_paths: List[str] = []

    # Validate base path format (basic check)
    if not path.startswith("/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Path must start with '/'")

    try:
        with zk_connection() as client:
            # Check if base path exists before starting recursion
            if not await client.exists_async(path):
                 raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Base path '{path}' not found in Zookeeper.")

            # Add the base path itself if it's valid and requested (e.g., path="/")
            # The recursive function adds children and their descendants.
            # If we want the base path included, add it here explicitly if it's not root
            # or handle root case. For simplicity, recursive adds all found paths.
            if path != "/": # Add the base path if it's not root. Root added below if exists.
                all_paths.append(path)
            elif await client.exists_async("/"): # Ensure root exists if path is "/"
                all_paths.append("/")


            await get_all_zk_nodes_recursive(client, path, all_paths)

        logger.info(f"Found {len(all_paths)} ZK paths under '{path}'.")
        return ZookeeperAllNodes(base_path=path, all_paths=sorted(list(set(all_paths)))) # Ensure uniqueness and sort

    except HTTPException: # Re-raise HTTP exceptions from zk_connection or validation
        raise
    except Exception as e:
        logger.exception(f"Failed to get all Zookeeper keys from path '{path}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while querying Zookeeper: {e}"
        )


@router.get("/key/{zk_path:path}", response_model=ZookeeperNode)
async def get_zookeeper_key_value(
    zk_path: str = FastApiPath(..., description="The full path of the Zookeeper node (e.g., /my/node)."),
    current_user: UserPublic = Depends(get_current_active_user) # Require authentication
):
    """
    Retrieves the data content of a specific Zookeeper node.
    Requires authentication. The path is part of the URL.
    """
    # Ensure the path starts with / because :path captures everything
    if not zk_path.startswith("/"):
        zk_path = "/" + zk_path

    logger.info(f"User '{current_user.username}' requested ZK key data for path: {zk_path}")

    try:
        with zk_connection() as client:
            data_bytes, znode_stat = await client.get_async(zk_path)
            logger.debug(f"ZNode Stat for {zk_path}: {znode_stat}")

            data_str: Optional[str] = None
            decode_error: Optional[str] = None
            if data_bytes is not None:
                try:
                    # Attempt to decode as UTF-8, common for ZK data
                    data_str = data_bytes.decode('utf-8')
                    logger.debug(f"Successfully decoded data for {zk_path}.")
                except UnicodeDecodeError as e:
                    logger.warning(f"Could not decode ZK data for path {zk_path} as UTF-8: {e}. Returning raw bytes representation might be needed or indicate binary data.")
                    # data_str = str(data_bytes) # Or return None and an error message
                    decode_error = f"Could not decode data as UTF-8: {e}"
                    # Return None for data if decoding fails completely? Or base64? Let's return None + error.

            return ZookeeperNode(path=zk_path, data=data_str, error=decode_error)

    except NoNodeError:
        logger.warning(f"ZK node not found for path {zk_path} requested by {current_user.username}.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Node path '{zk_path}' not found in Zookeeper.")
    except HTTPException: # Re-raise HTTP exceptions from zk_connection
        raise
    except KazooException as e:
         logger.error(f"Kazoo error getting ZK node {zk_path}: {e}")
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Zookeeper error: {e}")
    except Exception as e:
        logger.exception(f"Failed to get Zookeeper key '{zk_path}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while querying Zookeeper: {e}"
        )

# Optional: Add endpoint to close ZK connection explicitly if needed,
# or rely on app shutdown event.
@router.on_event("shutdown") # This needs to be in main.py usually
async def shutdown_zk_client():
     global zk_client
     if zk_client and zk_client.connected:
         logger.info("Shutting down Zookeeper client.")
         zk_client.stop()
         zk_client.close()
         zk_client = None
