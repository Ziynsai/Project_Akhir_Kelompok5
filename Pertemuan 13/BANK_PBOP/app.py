from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

class BankApp:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.secret_key = 'your_secret_key'
        self.init_db()
        self.setup_routes()

    def get_db_connection(self):
        conn = sqlite3.connect('bank.db')
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # Create Karyawan table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Karyawan (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        
        # Create Nasabah table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Nasabah (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                saldo REAL NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'aktif'
            )
        ''')
        
        # Create Transaksi table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Transaksi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nasabah_id INTEGER,
                jenis TEXT,
                jumlah REAL,
                FOREIGN KEY (nasabah_id) REFERENCES Nasabah (id)
            )
        ''')
        
        conn.commit()
        conn.close()

    def setup_routes(self):
        @self.app.route('/')
        def home():
            return render_template('login.html')

        @self.app.route('/login', methods=['POST'])
        def login():
            username = request.form['username']
            password = request.form['password']
            
            conn = self.get_db_connection()
            nasabah = conn.execute('SELECT * FROM Nasabah WHERE username = ? AND password = ?', (username, password)).fetchone()
            karyawan = conn.execute('SELECT * FROM Karyawan WHERE username = ? AND password = ?', (username, password)).fetchone()
            conn.close()
            
            if nasabah:
                if nasabah['status'] == 'beku':
                    return 'Akun Anda telah dibekukan.'
                session['user_id'] = nasabah['id']
                return redirect(url_for('nasabah_dashboard'))
            elif karyawan:
                session['user_id'] = karyawan['id']
                return redirect(url_for('karyawan_dashboard'))
            else:
                return 'Login Gagal'

        @self.app.route('/nasabah/dashboard')
        def nasabah_dashboard():
            if 'user_id' not in session:
                return redirect(url_for('login'))

            user_id = session['user_id']
            conn = self.get_db_connection()
            nasabah = conn.execute('SELECT * FROM Nasabah WHERE id = ?', (user_id,)).fetchone()
            conn.close()

            return render_template('nasabah.html', nasabah=nasabah)

        @self.app.route('/karyawan')
        def karyawan_dashboard():
            conn = self.get_db_connection()
            nasabah_list = conn.execute('SELECT * FROM Nasabah').fetchall()
            conn.close()
            return render_template('karyawan.html', nasabah_list=nasabah_list)

        @self.app.route('/nasabah/transfer', methods=['GET', 'POST'])
        def nasabah_transfer():
            if request.method == 'POST':
                nasabah_pengirim_id = session['user_id']
                nasabah_penerima_id = request.form['nasabah_penerima_id']
                jumlah_transfer = request.form['jumlah']

                if not nasabah_penerima_id or not jumlah_transfer:
                    return render_template('transfer.html', message='Semua field harus diisi.')

                try:
                    jumlah_transfer = float(jumlah_transfer)
                except ValueError:
                    return render_template('transfer.html', message='Jumlah harus berupa angka.')

                conn = self.get_db_connection()
                nasabah_penerima = conn.execute('SELECT * FROM Nasabah WHERE id = ?', (nasabah_penerima_id,)).fetchone()

                if not nasabah_penerima:
                    conn.close()
                    return render_template('transfer.html', message='Nasabah penerima tidak ditemukan.')

                nasabah_pengirim = conn.execute('SELECT * FROM Nasabah WHERE id = ?', (nasabah_pengirim_id,)).fetchone()
                if nasabah_pengirim['saldo'] < jumlah_transfer:
                    conn.close()
                    return render_template('transfer.html', message='Saldo Anda tidak cukup.')

                conn.execute('UPDATE Nasabah SET saldo = saldo - ? WHERE id = ?', (jumlah_transfer, nasabah_pengirim_id))
                conn.execute('UPDATE Nasabah SET saldo = saldo + ? WHERE id = ?', (jumlah_transfer, nasabah_penerima_id))
                
                conn.execute('INSERT INTO Transaksi (nasabah_id, jenis, jumlah) VALUES (?, ?, ?)', 
                             (nasabah_pengirim_id, 'transfer', -jumlah_transfer))
                # conn.execute('INSERT INTO Transaksi (nasabah_id, jenis, jumlah) VALUES (?, ?, ?)', 
                #              (nasabah_penerima_id, 'transfer', jumlah_transfer))

                conn.commit()
                conn.close()
                
                return redirect(url_for('nasabah_dashboard'))

            return render_template('transfer.html')

        @self.app.route('/nasabah/tarik', methods=['GET', 'POST'])
        def tarik():
            if 'user_id' not in session:
                return redirect(url_for('login'))

            user_id = session['user_id']
            conn = self.get_db_connection()
            nasabah = conn.execute('SELECT * FROM Nasabah WHERE id = ?', (user_id,)).fetchone()

            if request.method == 'POST':
                try:
                    amount = float(request.form['amount'])
                except ValueError:
                    return render_template('tarik.html', nasabah=nasabah, message='Jumlah harus berupa angka.')

                if amount <= 0:
                    return render_template('tarik.html', nasabah=nasabah, message='Jumlah tarik harus lebih besar dari nol.')

                if nasabah['saldo'] >= amount:
                    conn.execute('UPDATE Nasabah SET saldo = saldo - ? WHERE id = ?', (amount, nasabah['id']))
                    conn.execute('INSERT INTO Transaksi (nasabah_id, jenis, jumlah) VALUES (?, ?, ?)', (nasabah['id'], 'Tarik', amount))
                    conn.commit()
                    message = 'Tarik uang berhasil! Saldo Anda sekarang: {}'.format(nasabah['saldo'] - amount)
                else:
                    message = 'Saldo tidak cukup! Saldo Anda saat ini: {}'.format(nasabah['saldo'])

                conn.close()
                return render_template('tarik.html', nasabah=nasabah, message=message)

            return render_template('tarik.html', nasabah=nasabah)

        @self.app.route('/daftarkan_nasabah', methods=['GET', 'POST'])
        def daftarkan_nasabah():
            if request.method == 'POST':
                username = request.form['username']
                password = request.form['password']
                saldo = request.form['saldo']

                if not username or not password or not saldo:
                    return render_template('daftarkan_nasabah.html', message='Username, password, dan saldo tidak boleh kosong.')

                try:
                    saldo = float(saldo)
                except ValueError:
                    return render_template('daftarkan_nasabah.html', message='Saldo harus berupa angka.')

                conn = self.get_db_connection()
                
                existing_user = conn.execute('SELECT * FROM Nasabah WHERE username = ?', (username,)).fetchone()
                if existing_user:
                    conn.close()
                    return render_template('daftarkan_nasabah.html', message='Username sudah terdaftar.')

                conn.execute('INSERT INTO Nasabah (username, password, saldo, status) VALUES (?, ?, ?, ?)', (username, password, saldo, 'aktif'))
                conn.commit()
                conn.close()
                
                return redirect(url_for('karyawan_dashboard'))
            return render_template('daftarkan_nasabah.html')

        @self.app.route('/nasabah/riwayat_transaksi', methods=['GET'])
        def riwayat_transaksi():
            if 'user_id' not in session:
                return redirect(url_for('login'))

            user_id = session['user_id']
            conn = self.get_db_connection()
            transaksi_list = conn.execute('SELECT * FROM Transaksi WHERE nasabah_id = ? ORDER BY id DESC', (user_id,)).fetchall()
            conn.close()

            return render_template('riwayat_transaksi.html', transaksi_list=transaksi_list)

        @self.app.route('/bekukan_akun', methods=['GET', 'POST'])
        def bekukan_akun():
            if request.method == 'POST':
                nasabah_id = request.form['nasabah_id']
                conn = self.get_db_connection()
                conn.execute('UPDATE Nasabah SET status = ? WHERE id = ?', ('beku', nasabah_id))
                conn.commit()
                conn.close()
                return redirect(url_for('karyawan_dashboard'))
            return render_template('bekukan_akun.html')

        @self.app.route('/aktifkan_akun', methods=['GET', 'POST'])
        def aktifkan_akun():
            if request.method == 'POST':
                nasabah_id = request.form['nasabah_id']
                conn = self.get_db_connection()
                conn.execute('UPDATE Nasabah SET status = ? WHERE id = ?', ('aktif', nasabah_id))
                conn.commit()
                conn.close()
                return redirect(url_for('karyawan_dashboard'))
            return render_template('aktifkan_akun.html')

        @self.app.route('/logout', methods=['POST'])
        def logout():
            session.pop('user_id', None)
            return redirect(url_for('home'))

        @self.app.route('/transaksi', methods=['GET'])
        def lihat_transaksi():
            conn = self.get_db_connection()
            transaksi_list = conn.execute('SELECT * FROM Transaksi').fetchall()
            conn.close()
            return render_template('transaksi.html', transaksi_list=transaksi_list)

        @self.app.route('/update_saldo', methods=['GET', 'POST'])
        def update_saldo():
            if request.method == 'POST':
                nasabah_id = request.form['nasabah_id']
                new_saldo = request.form['saldo']

                if not nasabah_id or not new_saldo:
                    return render_template('update_saldo.html', message='ID Nasabah dan saldo tidak boleh kosong.')

                try:
                    new_saldo = float(new_saldo)
                except ValueError:
                    return render_template('update_saldo.html', message='Saldo harus berupa angka.')

                conn = self.get_db_connection()
                conn.execute('UPDATE Nasabah SET saldo = ? WHERE id = ?', (new_saldo, nasabah_id))
                conn.commit()
                conn.close()
                
                return redirect(url_for('karyawan_dashboard'))
            return render_template('update_saldo.html')

        @self.app.route('/hapus_transaksi', methods=['POST'])
        def hapus_transaksi():
            conn = self.get_db_connection()
            conn.execute('DELETE FROM Transaksi')
            conn.commit()
            conn.close()
            return redirect(url_for('karyawan_dashboard'))

    def run(self):
        self.app.run(debug=True)

if __name__ == '__main__':
    bank_app = BankApp()
    bank_app.run()
