import os
import sqlite3
import pandas as pd

SCRIPT_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(SCRIPT_DIR, "goahead.db")
CSV_PATH = os.path.join(
    os.path.expanduser("~"),
    "Downloads", "경삼관_접근성_엣지데이터_v1.csv",
)

NODE_TYPE_RULES = [
    ("엘리베이터", "엘리베이터"),
    ("계단",       "계단"),
    ("통로",       "통로"),
    ("장애인통로",  "통로"),
    ("복도",       "통로"),
    ("입구",       "건물입구"),
    ("시작노드",    "건물입구"),
]


def classify_node(name):
    for keyword, ntype in NODE_TYPE_RULES:
        if keyword in name:
            return ntype
    return "일반"


def load_csv():
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    print(f"[OK] CSV loaded: {len(df)} rows")
    return df


def extract_nodes(df):
    all_nodes = set(df["start_node"].tolist() + df["end_node"].tolist())
    rows = []
    for node_id in sorted(all_nodes):
        rows.append({
            "node_id": node_id,
            "name": node_id,
            "type": classify_node(node_id),
        })
    return pd.DataFrame(rows)


def insert_to_db(node_df, edge_df):
    conn = sqlite3.connect(DB_PATH)
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

    df = load_csv()

    edge_df = df.rename(columns={
        "start_node": "start_node",
        "end_node": "end_node",
        "distance_m": "distance_m",
        "stairs_count": "stairs_count",
        "step_height": "step_height",
        "door_type": "door_type",
        "obstacle_info": "obstacle_info",
    })
    edge_df["step_height"] = edge_df["step_height"].fillna("없음")
    edge_df["door_type"] = edge_df["door_type"].fillna("없음")
    edge_df["obstacle_info"] = edge_df["obstacle_info"].fillna("")

    node_df = extract_nodes(df)

    insert_to_db(node_df, edge_df)

    print("\n--- Nodes ---")
    print(node_df.to_string(index=False))
    print(f"\n--- Edges ({len(edge_df)} total) ---")
    print(edge_df.to_string(index=False))
