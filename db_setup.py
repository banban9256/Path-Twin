import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "goahead.db")


def create_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS edge")
    cur.execute("DROP TABLE IF EXISTS node")

    cur.execute("""
        CREATE TABLE node (
            node_id   TEXT PRIMARY KEY,
            name      TEXT NOT NULL,
            type      TEXT NOT NULL CHECK(type IN (
                          '건물 입구','교차로','횡단보도',
                          '엘리베이터','계단','버스정류장'
                      )),
            latitude  REAL NOT NULL,
            longitude REAL NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE edge (
            edge_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            start_node    TEXT NOT NULL REFERENCES node(node_id),
            end_node      TEXT NOT NULL REFERENCES node(node_id),
            distance_m    REAL NOT NULL,
            slope_type    TEXT NOT NULL CHECK(slope_type IN ('평지','오르막','내리막')),
            stairs_count  INTEGER NOT NULL DEFAULT 0,
            crosswalk     INTEGER NOT NULL DEFAULT 0,
            sidewalk_width TEXT NOT NULL CHECK(sidewalk_width IN ('좁음','보통','넓음')),
            confidence    TEXT NOT NULL CHECK(confidence IN ('직접조사','가상데이터','사용자 신고')),
            remarks       TEXT DEFAULT '',
            curb          INTEGER NOT NULL DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()
    print(f"[OK] DB created at {DB_PATH}")


if __name__ == "__main__":
    create_db()
