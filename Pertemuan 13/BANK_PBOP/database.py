# database.py
import sqlite3

def init_db():
    conn = sqlite3.connect('bank.db')
    cursor = conn.cursor()
    
    # Buat tabel Karyawan
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Karyawan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
    # Buat tabel Nasabah
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Nasabah (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            saldo REAL NOT NULL DEFAULT 0
        )
    ''')
    
    # Buat tabel Transaksi
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Transaksi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nasabah_id INTEGER,
            jenis TEXT,
            jumlah REAL,
            FOREIGN KEY (nasabah_id) REFERENCES Nasabah (id)
        )
    ''')
    
    cursor.execute('INSERT INTO Karyawan (username, password) VALUES (?, ?)', ('admin', 'admin123'))
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()