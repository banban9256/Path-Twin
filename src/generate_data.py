import os
import sys
import sqlite3
import pandas as pd

SCRIPT_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(os.path.dirname(SCRIPT_DIR), "goahead.db")

DEFAULT_CSV = os.path.join(os.path.dirname(SCRIPT_DIR), "data", "경삼관_최종_정규화데이터_완료.csv")


def get_csv_path():
    if len(sys.argv) > 1:
        return sys.argv[1]
    return os.environ.get("GOAHEAD_CSV", DEFAULT_CSV)


NODE_TYPE_RULES = [
    ("시작노드",    "시작지점"),
    ("엘리베이터", "엘리베이터"),
    ("계단",       "계단"),
    ("로비",       "로비"),
    ("연결통로",    "복도"),
    ("복도",       "복도"),
    ("문앞",       "출입구"),
    ("구름다리",    "구름다리"),
    ("열람실",     "열람실"),
    ("입구",       "입구"),
]


def classify_node(name):
    for keyword, ntype in NODE_TYPE_RULES:
        if keyword in name:
            return ntype
    return "일반"


def load_csv(csv_path):
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    print(f"[OK] CSV loaded: {len(df)} rows from {os.path.basename(csv_path)}")
    return df


def extract_nodes(df):
    all_nodes = sorted(set(df["start_node"].tolist() + df["end_node"].tolist()))
    rows = [{"node_id": n, "name": n, "type": classify_node(n)} for n in all_nodes]
    return pd.DataFrame(rows)


def insert_to_db(node_df, edge_df):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()
    cur.execute("DELETE FROM edge")
    cur.execute("DELETE FROM node")
    conn.commit()

    node_df.to_sql("node", conn, if_exists="append", index=False)
    edge_df.to_sql("edge", conn, if_exists="append", index=False)
    conn.commit()
    conn.close()
    print(f"[OK] Inserted {len(node_df)} nodes, {len(edge_df)} edges into DB")


if __name__ == "__main__":
    from db_setup import create_db
    create_db()

    csv_path = get_csv_path()
    df = load_csv(csv_path)

    edge_df = df.copy()
    edge_df["step_height"] = edge_df["step_height"].fillna("없음")
    edge_df["door_type"] = edge_df["door_type"].fillna("없음")
    edge_df["obstacle_info"] = edge_df["obstacle_info"].fillna("")

    node_df = extract_nodes(df)

    insert_to_db(node_df, edge_df)

    print("\n--- Nodes ---")
    print(node_df.to_string(index=False))
    print(f"\n--- Edges ({len(edge_df)} total) ---")
    print(edge_df[["start_node", "end_node", "edge_type", "distance_m",
                    "stairs_count", "step_height", "door_type"]].to_string(index=False))
