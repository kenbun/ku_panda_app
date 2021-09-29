# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, url_for
import ku_panda as ku
import datetime
import pandas as pd
from bs4 import BeautifulSoup
import numpy as np
import asyncio
import re

app = Flask(__name__)

@app.route('/')
def login():
  return render_template('login.html')

@app.route('/assign_list', methods=['POST'])
def assign_list():
  login, session = ku.login(request.form["username"], request.form["password"])
  loop = asyncio.new_event_loop()
  if login_successful(login) == 0:
    subject = ku.get_subject(login)
    subject = ku.get_url(subject,session,loop)
    assign = ku.get_yet_assign(subject, session, loop)
    yet_assign, dead_assign = assign_classification(assign)
    return render_template('assign_list.html', yet_list=yet_assign, dead_list=dead_assign, test_list=ku.get_yet_test(subject, session, loop))
  else:
    return redirect(url_for('/'))

def login_successful(html):
  bs = BeautifulSoup(html.text, 'html.parser')
  title = bs.find('title').text[0:5]
  if title == "PandA":
    return 0
  else:
    return 1

def assign_classification(assign):
  yet_assign = pd.DataFrame(columns=["subject", "title", "deadline", "status", "url"])
  dead_assign = pd.DataFrame(columns=["subject", "title", "deadline", "status", "url"])
  now = datetime.datetime.now()

  for index, var in assign.iterrows():
    deadline = re.split('[/: ]', var.deadline)
    if now < datetime.datetime(*[int(num) for num in deadline]):
      yet_assign = yet_assign.append({'subject':assign.iloc[index].subject, 'title':assign.iloc[index].title, 'deadline':assign.iloc[index].deadline, 'status':assign.iloc[index].status, 'url':assign.iloc[index].url}, ignore_index=True)
    else:
      dead_assign = dead_assign.append({'subject':assign.iloc[index].subject, 'title':assign.iloc[index].title, 'deadline':assign.iloc[index].deadline, 'status':assign.iloc[index].status, 'url':assign.iloc[index].url}, ignore_index=True)
  return yet_assign, dead_assign

if __name__ == '__main__':
  app.run(debug=True)