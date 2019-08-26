# -*- coding: utf-8 -*-

import hashlib
import sqlite3

class DatabaseManager:
    SCHEMA_FILE = './schema.sql'

    def __init__(self, path, create_db=False):
        self.db_path = path
        self.db_conn = None
        if create_db: self.__create_database_table()

    def __create_database_table(self):
        conn = self.connect()
        conn.executescript(open(self.SCHEMA_FILE).read(-1))
        conn.commit()

    def check_user_credentials(self, email, passwd):
        passwd = hashlib.md5(passwd.encode('utf-8')).hexdigest()
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', [email])
        row = cursor.fetchone()
        status = row and (row[3] == passwd)
        cursor.close()
        return status

    def get_user_data(self, email):
        data = None
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', [email])
        row = cursor.fetchone()
        if row: data = {'name': row[1], 'email': row[2]}
        cursor.close()
        return data

    def get_user_ideas(self, email, page=0):
        conn = self.connect()
        cursor = conn.cursor()
        ideas = []
        cursor.execute('''
                        SELECT *, (impact + ease + confidence) / 3.0 as avg_score
                        FROM ideas WHERE created_by = ?
                        ORDER BY avg_score
                        DESC LIMIT 10
                        OFFSET ?
                       ''', (email, page * 10))
        for row in cursor.fetchall():
            ideas.append({'id': row[0],
                          'content': row[2],
                          'impact': row[3],
                          'ease': row[4],
                          'confidence': row[5],
                          'created_at': row[6],
                          'average_score': row[7]})
        cursor.close()
        return ideas

    def get_idea(self, id):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('''
                        SELECT *, (impact + ease + confidence) / 3.0 as avg_score
                        FROM ideas WHERE id = ?
                       ''', [id])
        data = None
        row = cursor.fetchone()
        if row:
            data = {'id': row[0],
                    'content': row[2],
                    'impact': row[3],
                    'ease': row[4],
                    'confidence': row[5],
                    'created_at': row[6],
                    'average_score': row[7]}
        cursor.close()
        return data

    def create_user(self, name, email, passwd):
        conn = self.connect()
        cursor = conn.cursor()

        status = True
        try:
            passwd = hashlib.md5(passwd.encode('utf-8')).hexdigest()
            cursor.execute('INSERT INTO users(name, email, password) VALUES(?, ?, ?)', (name, email, passwd))
            cursor.close()
            conn.commit()
        except Exception:
            status = False

        return status

    def create_idea(self, email, content, impact, ease, confidence, creation_time):
        conn = self.connect()
        cursor = conn.cursor()

        status = -1
        try:
            cursor.execute('INSERT INTO ideas(created_by, content, impact, ease, confidence, creation_time) VALUES(?, ?, ?, ?, ?, ?)', (email, content, impact, ease, confidence, creation_time))
            status = cursor.lastrowid
            cursor.close()
            conn.commit()
        except Exception:
            pass

        return status

    def delete_idea(self, id, email):
        conn = self.connect()
        cursor = conn.cursor()

        status = True
        try:
            cursor.execute('DELETE FROM ideas WHERE id = ? AND created_by = ?', (id, email))
            conn.commit()
            status = cursor.rowcount > 0
        except Exception:
            status = False

        return status

    def update_idea(self, id, email, content, impact, ease, confidence):
        conn = self.connect()
        cursor = conn.cursor()

        status = True
        try:
            cursor.execute('UPDATE ideas SET content=?, impact=?, ease=?, confidence=? WHERE id=? AND created_by=?', (content, impact, ease, confidence, id, email))
            cursor.close()
            conn.commit()
        except Exception:
            status = False

        return status

    def connect(self):
        if not self.db_conn:
            self.db_conn = sqlite3.connect(self.db_path)
        return self.db_conn

    def disconnect(self):
        if self.db_conn:
            db_conn = self.db_conn
            self.db_conn = None
            db_conn.close()
        return True