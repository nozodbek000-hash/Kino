import json
import os

DB_FILE = "movies.json"


def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_movie(code: str, title: str, link: str, description: str = ""):
    db = load_db()
    db[code.upper()] = {
        "title": title,
        "link": link,
        "description": description,
        "code": code.upper()
    }
    save_db(db)
    return True


def delete_movie(code: str):
    db = load_db()
    code = code.upper()
    if code in db:
        del db[code]
        save_db(db)
        return True
    return False


def get_movie_by_code(code: str):
    db = load_db()
    return db.get(code.upper())


def search_movie_by_name(query: str):
    db = load_db()
    query = query.lower()
    results = []
    for code, movie in db.items():
        if query in movie["title"].lower():
            results.append(movie)
    return results


def get_all_movies():
    db = load_db()
    return list(db.values())


def get_stats():
    db = load_db()
    return len(db)
