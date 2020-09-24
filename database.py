import psycopg2

con = psycopg2.connect(
        database="database_name",
        user="user_name",
        password="your_password",
        host="your_host",
        port="your_port"
    )

cur = con.cursor()
cur.execute("CREATE TABLE table_name (user_id INT, employee_name TEXT, admin_marker INT, super_admin_marker INT)")
con.commit()
