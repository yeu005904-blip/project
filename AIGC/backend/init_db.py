import sqlite3

def create_database_table():
    conn = sqlite3.connect('scenic_spots.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS spots (
            city TEXT,
            spot_name TEXT,
            figure TEXT,
            reason TEXT,
            dialog TEXT,
            guide TEXT
        )
    ''')

    conn.commit()
    conn.close()
    print("数据库表创建成功")

if __name__ == "__main__":
    create_database_table()