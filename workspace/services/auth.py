from flask import Flask, request
import sqlite3

app = Flask(__name__)

@app.get('/users/<user_id>')
def get_user(user_id):
    db = sqlite3.connect('app.db')
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return db.execute(query).fetchone()
