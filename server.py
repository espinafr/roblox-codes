#env\Scripts\python.exe
# -*- coding: utf-8 -*-

import os
from flask import Flask, request, render_template, abort, url_for, redirect, session, json
from datetime import datetime
import sqlite3

app = Flask(__name__, static_folder='public', template_folder='views')

app.secret_key = os.environ.get('SECRET')
app.config['APICODE'] = os.environ.get('APICODE')
app.config['USERS'] = {os.environ.get('USER'): os.environ.get('SENHA')}

def access_db(command: str, params, method: str):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(command, params)
    results = cursor.fetchall() if method=='f' else conn.commit()
    conn.close()
    return results

def expired(date, id):
    if date != "" and datetime.strptime(date,"%Y-%m-%d") < datetime.now():
        access_db('DELETE FROM codiguins WHERE id = ?', (id,), 'c')
        return True
    else:
        return False

@app.route('/') # Login
def index():
    if 'username' in session:
        return redirect(url_for('admin'))
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    if username in app.config['USERS'] and app.config['USERS'][username] == password:
        session['username'] = username
        return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 
    return json.dumps({'success':False}), 400, {'ContentType':'application/json'} 

@app.route('/admin')
def admin():
    if not 'username' in session:
        abort(401)
    codigos = access_db('SELECT * FROM codiguins', (), 'f')
    for codigo in codigos:
        expired(codigo[4], codigo[0])
    return render_template('admin.html', username=session['username'], codigos=codigos)

@app.route('/admin/post', methods=['POST'])
def adminpost():
    if not 'username' in session:
        abort(401)
    if request.method == 'POST':
        tipo = request.form['tipo']
        codigo = request.form['codigo']
        num = request.form['num']
        exp = request.form['exp']

        access_db('INSERT INTO codiguins (codigo, tipo, num, exp) VALUES (?, ?, ?, ?)', (codigo, tipo, num, exp), 'c')
    return redirect(url_for('admin'))

@app.route('/admin/get/<codigo>', methods=['POST'])
def adminget(codigo):
    if request.json['apicode'] == app.config['APICODE']:
        rawData = access_db('SELECT * FROM codiguins WHERE codigo = ? LIMIT 1', (codigo,), 'f')
        data = {}
        if not rawData == [] and not expired(rawData[0][4], rawData[0][0]):
            data = {
                "id":  rawData[0][0],
                "codigo": rawData[0][1],
                "tipo": rawData[0][2],
                "numero": rawData[0][3]
            }
        return json.dumps(data)
    else:
        abort(401)

@app.route('/admin/delete/<codid>', methods=['POST'])
def admindelete(codid):
    if not 'username' in session:
        abort(401)
    access_db('DELETE FROM codiguins WHERE id = ?', (codid,), 'c')
    return redirect(url_for('admin'))

if __name__ == '__main__':
    access_db('''
        CREATE TABLE IF NOT EXISTS codiguins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT,
            tipo TEXT,
            num TEXT,
            exp INTEGER
        )
    ''', (), 'c') # criando a table
    app.run(debug=True)