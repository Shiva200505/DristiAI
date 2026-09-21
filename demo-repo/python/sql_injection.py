from flask import request


def find_user(db):
    user_id = request.args["id"]
    # VULNERABLE: DRISHTI-SQL-001 / CWE-89
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return db.execute(query).fetchone()

# Expected fix: db.execute("SELECT ... WHERE id = ?", (user_id,))
