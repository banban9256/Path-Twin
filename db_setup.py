import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "goahead.db")


def create_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS edge")
    cur.execute("DROP TABLE IF EXISTS node")

    cur.execute("""
        CREATE TABLE node (
            node_id   TEXT PRIMARY KEY,
            name      TEXT NOT NULL,
            type      TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE edge (
            edge_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            start_node    TEXT NOT NULL REFERENCES node(node_id),
            end_node      TEXT NOT NULL REFERENCES node(node_id),
            edge_type     TEXT NOT NULL,
            distance_m    REAL NOT NULL,
            stairs_count  INTEGER NOT NULL DEFAULT 0,
            step_height   TEXT NOT NULL DEFAULT '없음',
            door_type     TEXT NOT NULL DEFAULT '없음',
            obstacle_info TEXT DEFAULT ''
        )
    """)

    conn.commit()
    conn.close()
    print(f"[OK] DB created at {DB_PATH}")


if __name__ == "__main__":
    create_db()
