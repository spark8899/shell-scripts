#!/bin/env python3
# pip3 install PyMySQL python-dotenv
# .env # file
"""
DB_HOST=127.0.0.1
DB_USER=root
DB_PASS=root123
DB_NAME=db01
"""

import os, pymysql, sys
from pathlib import Path
from dotenv import load_dotenv

exec_directory = Path(__file__).resolve().parent
os.chdir(exec_directory)
load_dotenv()

# ==================== 1. DATABASE CONFIGURATION ====================
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASS"),
    "database": os.getenv("DB_NAME"),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor
}

def get_db_connection():
    """Establish DB connection"""
    try:
        return pymysql.connect(**DB_CONFIG)
    except pymysql.MySQLError as e:
        print(f"Error: Connection failed. {e}", file=sys.stderr)
        sys.exit(1)

def check_user_exists(cursor, user_id):
    """Check if target user_id exists"""
    sql = "SELECT user_id FROM user WHERE user_id = %s"
    cursor.execute(sql, (user_id,))
    return cursor.fetchone() is not None

# ==================== 2. FORMAT 1: TREE STYLE ====================
def print_as_tree(cursor, user_id):
    """Print hierarchy in tree format"""
    print(f"{user_id}")
    _print_tree_recursive(cursor, user_id, prefix="")

def _print_tree_recursive(cursor, current_user_id, prefix=""):
    sql = "SELECT user_id FROM user WHERE inviter_user_id = %s"
    cursor.execute(sql, (current_user_id,))
    children = cursor.fetchall()

    count = len(children)
    for index, row in enumerate(children):
        child_id = row["user_id"]
        is_last = (index == count - 1)
        connector = "└── " if is_last else "├── "

        print(f"{prefix}{connector}{child_id}")

        # Adjust prefix indentation for next depth layer
        new_prefix = prefix + ("    " if is_last else "│   ")
        _print_tree_recursive(cursor, child_id, new_prefix)

# ==================== 3. FORMAT 2: FLAT COMMA-SEPARATED ====================
def print_as_flat(cursor, user_id):
    """Print all downstream IDs comma-separated"""
    result_ids = []
    _collect_ids_recursive(cursor, user_id, result_ids)

    if not result_ids:
        print("(No invitees found)")
    else:
        print(",".join(map(str, result_ids)))

def _collect_ids_recursive(cursor, current_user_id, result_ids):
    sql = "SELECT user_id FROM user WHERE inviter_user_id = %s"
    cursor.execute(sql, (current_user_id,))
    children = cursor.fetchall()

    for row in children:
        child_id = row["user_id"]
        result_ids.append(child_id)
        _collect_ids_recursive(cursor, child_id, result_ids)

# ==================== 4. MAIN EXECUTION & SYS INPUT VALIDATION ====================
def print_usage():
    """Print usage manual"""
    print("\nUsage: python show_tree.py <user_id> [format]")
    print("Formats: 'tree' (default) | 'flat'\n")

if __name__ == "__main__":
    # Validate argument count
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Error: Invalid arguments.", file=sys.stderr)
        print_usage()
        sys.exit(1)

    # Validate user_id type
    try:
        target_user_id = int(sys.argv[1])
    except ValueError:
        print("Error: <user_id> must be an integer.", file=sys.stderr)
        sys.exit(1)

    # Validate format type
    output_format = "tree"  # Default fallback
    if len(sys.argv) == 3:
        output_format = sys.argv[2].lower()
        if output_format not in ["tree", "flat"]:
            print("Error: Invalid format. Use 'tree' or 'flat'.", file=sys.stderr)
            sys.exit(1)

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            if not check_user_exists(cursor, target_user_id):
                print(f"User {target_user_id} not found.")
                sys.exit(0)

            # Executing query based on format
            if output_format == "tree":
                print(f"[Tree Format for User {target_user_id}]")
                print("-" * 40)
                print_as_tree(cursor, target_user_id)
                print("-" * 40)
            elif output_format == "flat":
                print(f"[Flat Format for User {target_user_id}]")
                print("-" * 40)
                print_as_flat(cursor, target_user_id)
                print("-" * 40)

    finally:
        connection.close()
