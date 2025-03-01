import sqlite3
from flask import Flask


DATABASE = 'new_database.db'  #Main database initialization

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn

