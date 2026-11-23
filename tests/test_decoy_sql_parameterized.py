import sqlite3
import eval.decoys.decoy_sql_parameterized as dsp

def test_decoy_sql_parameterized():
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()
    cur.execute("CREATE TABLE user (id INTEGER PRIMARY KEY, username TEXT, email TEXT)")
    cur.execute("CREATE TABLE txn (id INTEGER PRIMARY KEY, account_id INTEGER, description TEXT, amount REAL)")
    
    # Test insert_user
    user_id = dsp.insert_user(conn, "alice", "alice@example.com")
    assert user_id == 1
    
    # Test get_user_by_name
    user = dsp.get_user_by_name(conn, "alice")
    assert user == (1, "alice")
    
    # Insert a transaction
    cur.execute("INSERT INTO txn (account_id, description, amount) VALUES (?, ?, ?)", (1, "Lunch payment", 15.5))
    conn.commit()
    
    # Test search_transactions
    txns = dsp.search_transactions(conn, 1, "Lunch")
    assert len(txns) == 1
    assert txns[0][1] == "Lunch payment"
