import psycopg2

try:
    # Connect as postgres superuser
    conn = psycopg2.connect(user='postgres', host='localhost', password='1919131')
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Create user if not exists
    cursor.execute("SELECT 1 FROM pg_roles WHERE rolname='nume'")
    if not cursor.fetchone():
        cursor.execute("CREATE USER nume WITH PASSWORD '1919131'")
        print('Created user: nume')
    else:
        print('User nume already exists')
    
    # Create database if not exists
    cursor.execute("SELECT 1 FROM pg_database WHERE datname='nume'")
    if not cursor.fetchone():
        cursor.execute("CREATE DATABASE nume OWNER nume")
        print('Created database: nume')
    else:
        print('Database nume already exists')
    
    # Grant privileges
    cursor.execute("GRANT ALL PRIVILEGES ON DATABASE nume TO nume")
    print('Granted privileges to nume')
    
    cursor.close()
    conn.close()
    print('Database setup complete!')
except Exception as e:
    print(f'Error: {e}')