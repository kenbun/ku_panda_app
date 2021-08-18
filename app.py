# -*- coding: utf-8 -*-
from flask import Flask, render_template, request
import ku_panda as ku

app = Flask(__name__)

@app.route('/')
def index():
  return 'hello, world'

@app.route('/login')
def login():
  return render_template('login.html')

@app.route('/assign_list', methods=['POST'])
def assign_list():
  print(request.data)
  login, session = ku.login(request.form["username"], request.form["password"])
  return render_template('assign_list.html', status=login)

if __name__ == '__main__':
    app.run(debug=True)