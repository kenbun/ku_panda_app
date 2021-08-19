import requests
import time
from bs4 import BeautifulSoup
import pandas as pd

def login(username, password):
  url="https://cas.ecs.kyoto-u.ac.jp/cas/login?service=https%3A%2F%2Fpanda.ecs.kyoto-u.ac.jp%2Fsakai-login-tool%2Fcontainer"
  login_data = {
    "username" : username,
    "password" : password,
    "execution" : "e1s1",
    "_eventId" : "submit",
    "submit": "ログイン",
  }

  session = requests.session()
  response = session.get(url)

  bs = BeautifulSoup(response.text, 'html.parser')

  authenticity_token = bs.find(attrs={'name': 'lt'}).get('value')
  login_data['lt'] = authenticity_token

  response_cookie = response.cookies
  login_url = "https://cas.ecs.kyoto-u.ac.jp/cas/login?service=https%3A%2F%2Fpanda.ecs.kyoto-u.ac.jp%2Fsakai-login-tool%2Fcontainer"
  login = session.post(login_url, data=login_data, cookies=response_cookie)
  # time.sleep(2)
  return login, session

def get_subject(html):
  bs = BeautifulSoup(html.text, 'html.parser')
  menu = bs.find_all('li', class_='fav-sites-entry')
  subject = pd.DataFrame(columns=['title', 'url'])
  for sub in menu:
    span=sub.find('a', title=True)
    title, href = span.get('title'), span.get('href')
    if(title[0] == '['):
      subject = subject.append({'title':title, 'url':href}, ignore_index=True)
  return subject

def get_assign_url(subject, session):
  new_subject = subject.assign(assign_url = "")
  for index, col in subject.iterrows():
    html = session.get(col.url)
    bs = BeautifulSoup(html.text, 'html.parser')
    assign_div = bs.find('div', class_="Mrphs-toolsNav__menuitem--icon icon-sakai--sakai-assignment-grades").parent
    assign_url = assign_div.get('href')
    new_subject["assign_url"].iloc[index] = assign_url
  return new_subject

def get_yet_assign(subject, session):
  assign = pd.DataFrame(columns=["subject", "title", "deadline", "status", "url"])
  for index, col in subject.iterrows():
    html = session.get(col.assign_url)
    bs = BeautifulSoup(html.text, 'html.parser')
    table = bs.find('table',class_="table table-hover table-striped table-bordered" )
    if bool(table):
      due = table.find_all('td', headers="status")
      for t in due:
        status = t.get_text().replace('\t','').replace('\n', '')
        title = t.parent.find('td', headers="title").get_text().replace('\t','').replace('\n', '')
        until = t.parent.find('td', headers="dueDate").get_text().replace('\t','').replace('\n', '')
        if str(status[0:4]) != r"提出日時":
          assign = assign.append({'subject':col.title, 'title':title, 'deadline':until, 'status':status, 'url':col.assign_url}, ignore_index=True)
  return assign
