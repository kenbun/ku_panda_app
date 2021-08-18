# -*- coding: utf-8 -*-
from flask import Flask, render_template, request
import ku_panda as ku
from bs4 import BeautifulSoup

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
  status = login_successful(login)
  if status == 0:
    return render_template('assign_list.html', status=status)
  else:
    return redirect(url_for('login'))

def login_successful(html):
  bs = BeautifulSoup(html.text, 'html.parser')
  title = bs.find('title').text[0:5]
  if title = "PandA":
    return 0
  else:
    return 1

if __name__ == '__main__':
    app.run(debug=True)