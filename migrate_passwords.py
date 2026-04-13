"""
Password Migration Script
This script migrates existing plain-text passwords to bcrypt hashed passwords.
Run this once after updating the codebase.
"""
import pymysql
import re
from utils.db_utils import get_db_connection
from utils.auth import hash_password, verify_password
from utils.logger import logger


def is_bcrypt_hash(password):
    """
    Check if password is already a bcrypt hash

    Args:
        password: Password string to check

    Returns:
        True if it looks like a bcrypt hash, False otherwise
    """
    # bcrypt hashes are typically 60 characters and start with $2a$, $2b$, or $2y$
    bcrypt_pattern = r'^\$2[aby]\$\d{2}\$[A-Za-z0-9./]{53}$'
    return bool(re.match(bcrypt_pattern, password))


def migrate_passwords():
    """Migrate all plain-text passwords to bcrypt hashes"""
    logger.info("Starting password migration...")

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # Get all users with plain-text passwords
            cursor.execute("SELECT id, username, password FROM user")
            users = cursor.fetchall()

            migrated_count = 0
            skipped_count = 0
            error_count = 0

            for user in users:
                user_id = user['id']
                username = user['username']
                password = user['password']

                # Check if password is already hashed
                if is_bcrypt_hash(password):
                    skipped_count += 1
                    logger.debug(f"Skipped already hashed password for user: {username}")
                    continue

                try:
                    # Hash the password
                    hashed_password = hash_password(password)

                    # Update the database
                    update_query = "UPDATE user SET password = %s WHERE id = %s"
                    cursor.execute(update_query, (hashed_password, user_id))
                    migrated_count += 1
                    logger.info(f"Migrated password for user: {username}")
                except Exception as e:
                    error_count += 1
                    logger.error(f"Failed to migrate password for user {username}: {e}")

            connection.commit()
            logger.info(f"Migration complete - Migrated: {migrated_count}, Skipped: {skipped_count}, Errors: {error_count}")
            print(f"\n{'='*50}")
            print(f"Migration Summary:")
            print(f"  ✓ Migrated: {migrated_count} passwords")
            print(f"  ⊘ Skipped:  {skipped_count} passwords (already hashed)")
            print(f"  ✗ Errors:   {error_count} passwords")
            print(f"{'='*50}\n")

    except Exception as e:
        logger.error(f"Password migration failed: {e}")
        print(f"Error: {e}")
    finally:
        connection.close()


if __name__ == "__main__":
    print("⚠️  WARNING: This will migrate all plain-text passwords to bcrypt hashes.")
    print("⚠️  Already hashed passwords will be skipped.\n")

    confirm = input("Continue? Type 'yes' to confirm: ")
    if confirm.lower() == 'yes':
        migrate_passwords()
    else:
        print("Migration cancelled.")

