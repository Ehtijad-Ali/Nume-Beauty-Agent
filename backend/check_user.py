import psycopg2

try:
    conn = psycopg2.connect(user='postgres', host='localhost', password='1919131')
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM pg_roles WHERE rolname='nume'")
    exists = cursor.fetchone()
    print('User exists:', exists is not None)
    cursor.close()
    conn.close()
except Exception as e:
    print(f'Error: {e}')