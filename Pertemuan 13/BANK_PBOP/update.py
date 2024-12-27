import sqlite3

def add_status_column():
    conn = sqlite3.connect('bank.db')  # Ganti dengan nama database Anda
    cursor = conn.cursor()
    
    # Menambahkan kolom status
    cursor.execute("ALTER TABLE Nasabah ADD COLUMN status TEXT DEFAULT 'aktif';")
    
    conn.commit()
    conn.close()

add_status_column()