import time
import pymysql

def run(db_host: str, db_user: str, db_password: str, db_name: str,
        num_connections: int = 50, duration_seconds: int = 60, **kwargs) -> dict:
    """
    Opens many MySQL connections and holds them open (never returned to a
    pool) to exhaust available connections.
    """
    connections = []
    try:
        for _ in range(num_connections):
            conn = pymysql.connect(host=db_host, user=db_user, password=db_password, database=db_name)
            connections.append(conn)
        time.sleep(duration_seconds)
    finally:
        for conn in connections:
            conn.close()

    return {
        "connections_opened": len(connections),
        "mechanism": "held open connections, simulating a connection leak",
    }