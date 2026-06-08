# database.py
import sqlite3
from config import DB_NAME

def get_conn():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            lang TEXT DEFAULT 'uz',
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name_uz TEXT NOT NULL,
            name_ru TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name_uz TEXT NOT NULL,
            name_ru TEXT DEFAULT '',
            category_id INTEGER REFERENCES categories(id),
            file_id TEXT NOT NULL,
            message_id INTEGER,
            year INTEGER,
            description_uz TEXT DEFAULT '',
            description_ru TEXT DEFAULT '',
            added_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    default_cats = [
        ("Akshn", "Экшн"),
        ("Komediya", "Комедия"),
        ("Drama", "Драма"),
        ("Fantastika", "Фантастика"),
        ("Qo'rqinchli", "Ужасы"),
        ("Multfilm", "Мультфильм"),
        ("Hujjatli", "Документальный"),
        ("Jangovar", "Боевик"),
        ("Romantik", "Романтика"),
        ("Triller", "Триллер"),
    ]
    c.executemany("INSERT OR IGNORE INTO categories (name_uz, name_ru) VALUES (?, ?)", default_cats)
    conn.commit()
    conn.close()

# ── Users ─────────────────────────────────────────────────
def save_user(user_id, username, full_name, lang="uz"):
    conn = get_conn()
    conn.execute(
        "INSERT OR IGNORE INTO users (id, username, full_name, lang) VALUES (?,?,?,?)",
        (user_id, username, full_name, lang)
    )
    conn.commit()
    conn.close()

def get_user_lang(user_id):
    conn = get_conn()
    row = conn.execute("SELECT lang FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    return row["lang"] if row else "uz"

def set_user_lang(user_id, lang):
    conn = get_conn()
    conn.execute("UPDATE users SET lang=? WHERE id=?", (lang, user_id))
    conn.commit()
    conn.close()

def count_users():
    conn = get_conn()
    n = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    return n

# ── Movies ────────────────────────────────────────────────
def add_movie(name_uz, name_ru, category_id, file_id, message_id, year, desc_uz, desc_ru, admin_id):
    conn = get_conn()
    cur = conn.execute(
        """INSERT INTO movies
           (name_uz, name_ru, category_id, file_id, message_id, year, description_uz, description_ru, added_by)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (name_uz, name_ru, category_id, file_id, message_id, year, desc_uz, desc_ru, admin_id)
    )
    conn.commit()
    mid = cur.lastrowid
    conn.close()
    return mid

def delete_movie(movie_id):
    conn = get_conn()
    conn.execute("DELETE FROM movies WHERE id=?", (movie_id,))
    conn.commit()
    conn.close()

def get_movie(movie_id):
    conn = get_conn()
    row = conn.execute(
        """SELECT m.*, c.name_uz as cat_uz, c.name_ru as cat_ru
           FROM movies m LEFT JOIN categories c ON m.category_id=c.id
           WHERE m.id=?""", (movie_id,)
    ).fetchone()
    conn.close()
    return row

def search_movies(query):
    conn = get_conn()
    like = f"%{query}%"
    rows = conn.execute(
        """SELECT m.*, c.name_uz as cat_uz, c.name_ru as cat_ru
           FROM movies m LEFT JOIN categories c ON m.category_id=c.id
           WHERE m.name_uz LIKE ? OR m.name_ru LIKE ?
           ORDER BY m.name_uz LIMIT 50""",
        (like, like)
    ).fetchall()
    conn.close()
    return rows

def get_movies_by_category(cat_id, limit=8, offset=0):
    conn = get_conn()
    rows = conn.execute(
        """SELECT m.*, c.name_uz as cat_uz, c.name_ru as cat_ru
           FROM movies m LEFT JOIN categories c ON m.category_id=c.id
           WHERE m.category_id=? ORDER BY m.created_at DESC LIMIT ? OFFSET ?""",
        (cat_id, limit, offset)
    ).fetchall()
    conn.close()
    return rows

def count_by_category(cat_id):
    conn = get_conn()
    n = conn.execute("SELECT COUNT(*) FROM movies WHERE category_id=?", (cat_id,)).fetchone()[0]
    conn.close()
    return n

def get_new_movies(limit=10):
    conn = get_conn()
    rows = conn.execute(
        """SELECT m.*, c.name_uz as cat_uz, c.name_ru as cat_ru
           FROM movies m LEFT JOIN categories c ON m.category_id=c.id
           ORDER BY m.created_at DESC LIMIT ?""", (limit,)
    ).fetchall()
    conn.close()
    return rows

def count_movies():
    conn = get_conn()
    n = conn.execute("SELECT COUNT(*) FROM movies").fetchone()[0]
    conn.close()
    return n

# ── Categories ────────────────────────────────────────────
def get_categories():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM categories ORDER BY id").fetchall()
    conn.close()
    return rows

def get_category(cat_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM categories WHERE id=?", (cat_id,)).fetchone()
    conn.close()
    return row
