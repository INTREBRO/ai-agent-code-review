"""Small, parameterized lookup for a review demonstration."""


def find_user(connection, user_id: str):
    return connection.execute(
        "SELECT id, email FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
