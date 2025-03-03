from db import get_db_connection  # Import database connection function
from werkzeug.security import generate_password_hash, check_password_hash  # For password hashing
import sqlite3
import datetime

class User:
    def __init__(self, id, username, password_hash, role, total_credits, last_reset):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.role = role
        self.total_credits = total_credits
        self.last_reset = last_reset

    @staticmethod
    def create_user(username, password, role='user'):
        conn = get_db_connection()
        cursor = conn.cursor()
        password_hash = generate_password_hash(password)  # Hash the password
        try:
            cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                           (username, password_hash, role))
            conn.commit()
            user_id = cursor.lastrowid  # Get the ID of the newly inserted user
            conn.close()
            return user_id
        except sqlite3.IntegrityError:  # Username already exists (UNIQUE constraint)
            conn.close()
            return None  # Indicate registration failure due to username conflict
    @staticmethod
    def decrement_credits(user_id):
        """Atomic credit decrement with transaction"""
        conn = get_db_connection()
        try:
            conn.execute("BEGIN TRANSACTION")
            # Add check for credits > 0
            conn.execute(
                "UPDATE users SET credits = credits - 1 WHERE id = ? AND credits > 0",
                (user_id,)
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            conn.rollback()
            print(f"Database error in decrement_credits: {e}")
            return False
        finally:
            conn.close()

    # Add this new method
    @staticmethod
    def reset_all_credits():
        """Reset credits for all users to 20"""
        conn = get_db_connection()
        try:
            conn.execute(
                "UPDATE users SET credits = 20, last_reset = CURRENT_TIMESTAMP"
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Credit reset failed: {e}")
            return False
        finally:
            conn.close()
    @staticmethod
    def get_user_by_username(username):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return User(id=row['id'], username=row['username'], password_hash=row['password_hash'],
                        role=row['role'], total_credits=row['credits'], last_reset=row['last_reset'])
        return None

    def check_password(self, password):
        # Debugging: Print the password and hashed password
        print(f"Password: {password}")
        print(f"Hashed Password: {self.password_hash}")
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def get_user_by_id(user_id):  # New method to fetch user by ID
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return User(id=row['id'], username=row['username'], password_hash=row['password_hash'],
                        role=row['role'], total_credits=row['credits'], last_reset=row['last_reset'])
        return None
    
    @staticmethod
    def decrement_credits(user_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE users SET credits = credits - 1 WHERE id = ?", (user_id,))
            conn.commit()
        except sqlite3.Error as e:
            print(f"Database error in decrement_credits: {e}") # Log the error for debugging
            conn.rollback() # Rollback in case of error
            return False # Indicate failure
        finally:
            conn.close()
        return True # Indicate success if no exception

##Document class
class Document:
  
    # Represents a scanned document and its metadata, stored in the 'documents' table.
    
    def __init__(self, filename, filepath, user_id, scan_date=None, id=None):
        """
        Initializes a Document object.

        Args:
            filename (str): Original filename of the uploaded document.
            filepath (str): Server filepath where the document is stored.
            user_id (int): ID of the user who uploaded the document (foreign key to users table).
            scan_date (datetime, optional): Date and time of scan. Defaults to current time if None.
            id (int, optional): Document ID (for database, auto-generated upon saving). Defaults to None.
        """
        self.id = id  # Document ID (integer, primary key, auto-generated by DB)
        self.filename = filename  # Filename (string, not null)
        self.filepath = filepath  # Filepath on server (string, not null)
        self.user_id = user_id  # User ID of uploader (integer, foreign key to users table, not null)
        self.scan_date = scan_date or datetime.datetime.now()  # Scan datetime (datetime, defaults to now)

    def save(self):
        """
        Saves the Document object to the 'documents' table in the database.
        Inserts a new row if the document is new (self.id is None).
        Updates self.id with the database-generated ID after successful insertion.

        Returns:
            bool: True if saving was successful, False otherwise (e.g., database error).
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO documents (filename, filepath, user_id, scan_date) VALUES (?, ?, ?, ?)",
                (self.filename, self.filepath, self.user_id, self.scan_date)
            )
            conn.commit()
            self.id = cursor.lastrowid  # Retrieve the auto-generated ID after INSERT
            return True # Indicate successful save
        except sqlite3.Error as e:
            print(f"Database error in Document.save: {e}") # Log database error
            conn.rollback() # Rollback transaction on error
            return False # Indicate save failed
        finally:
            conn.close() # Ensure connection is closed

    @staticmethod
    def get_document_by_id(document_id):
        """
        Retrieves a Document object from the database based on its ID.

        Args:
            document_id (int): The ID of the document to retrieve.

        Returns:
            Document or None: A Document object if found, None otherwise.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        document = None # Initialize document to None (in case not found)
        try:
            cursor.execute("SELECT * FROM documents WHERE id = ?", (document_id,))
            row = cursor.fetchone() # Fetch one result row
            if row: # If a row was found (document exists)
                document = Document( # Create a Document object from the database row
                    id=row['id'],
                    filename=row['filename'],
                    filepath=row['filepath'],
                    user_id=row['user_id'],
                    scan_date=row['scan_date']
                )
        except sqlite3.Error as e:
            print(f"Database error in Document.get_document_by_id: {e}") # Log database error
        finally:
            conn.close() # Ensure connection is closed
        return document # Return Document object (or None if not found)
    @classmethod
    def get_by_id(cls, doc_id):
        """Get document by ID (alias for existing get_document_by_id)"""
        return cls.get_document_by_id(doc_id)

    @classmethod
    def get_all_documents(cls):
        """Get all documents from the database"""
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        documents = []
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents")
            rows = cursor.fetchall()
            for row in rows:
                documents.append(Document(
                    id=row['id'],
                    filename=row['filename'],
                    filepath=row['filepath'],
                    user_id=row['user_id'],
                    scan_date=row['scan_date']
                ))
        except sqlite3.Error as e:
            print(f"Database error in get_all_documents: {e}")
        finally:
            conn.close()
        return documents

    @classmethod
    def get_by_filename(cls, filename):
        """Get document by filename"""
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        document = None
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents WHERE filename = ?", (filename,))
            row = cursor.fetchone()
            if row:
                document = Document(
                    id=row['id'],
                    filename=row['filename'],
                    filepath=row['filepath'],
                    user_id=row['user_id'],
                    scan_date=row['scan_date']
                )
        except sqlite3.Error as e:
            print(f"Database error in get_by_filename: {e}")
        finally:
            conn.close()
        return document