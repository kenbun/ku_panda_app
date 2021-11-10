import requests
import time
from bs4 import BeautifulSoup
import pandas as pd
import logging
import asyncio

async def run(loop, session, urls):
  sem = asyncio.Semaphore(5)
  async def run_get(session, url):
    async with sem:
      return await loop.run_in_executor(None, session.get, url)

  tasks = [run_get(session, url) for url in urls]
  return await asyncio.gather(*tasks)

def login(username, password):
  url="https://panda.ecs.kyoto-u.ac.jp/cas/login?service=https%3A%2F%2Fpanda.ecs.kyoto-u.ac.jp%2Fsakai-login-tool%2Fcontainer"
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
  login = session.post(url, data=login_data, cookies=response_cookie)
  return login, session

def get_subject(html, semester):
  bs = BeautifulSoup(html.text, 'html.parser')
  menu = bs.find_all('li', class_='fav-sites-entry')
  subject = pd.DataFrame(columns=['title', 'url'])
  for sub in menu:
    span=sub.find('a', title=True)
    title, href = span.get('title'), span.get('href')
    if(title[0] == '['):
      if(title[5:7] == semester):
        subject = subject.append({'title':title, 'url':href}, ignore_index=True)
  return subject

def get_assign_url(subject, session, loop):
  new_subject = subject.assign(assign_url = "")
  task = loop.run_until_complete(run(loop, session, subject.url))
  for index, html in enumerate(task):
    bs = BeautifulSoup(html.text, 'html.parser')
    assign_div = bs.find('div', class_="Mrphs-toolsNav__menuitem--icon icon-sakai--sakai-assignment-grades")
    if assign_div != None:
      assign_url = assign_div.parent.get('href')
      new_subject["assign_url"].iloc[index] = assign_url+"?criteria=assignment_status&panel=Main&sakai_action=doSort"
  return new_subject

def get_test_url(subject, session, loop):
  new_subject = subject.assign(test_url = "")
  task = loop.run_until_complete(run(loop, session, subject.url))
  for index, html in enumerate(task):
    bs = BeautifulSoup(html.text, 'html.parser')
    test_div = bs.find('div', class_="Mrphs-toolsNav__menuitem--icon icon-sakai--sakai-samigo")
    if test_div != None:
      test_url = test_div.parent.get('href')
      new_subject["test_url"].iloc[index] = test_url
  return new_subject

def get_url(subject, session, loop):
  new_subject = subject.assign(assign_url = "", test_url="")
  task = loop.run_until_complete(run(loop, session, subject.url))
  for index, html in enumerate(task):
    bs = BeautifulSoup(html.text, 'html.parser')
    assign_div = bs.find('div', class_="Mrphs-toolsNav__menuitem--icon icon-sakai--sakai-assignment-grades")
    test_div = bs.find('div', class_="Mrphs-toolsNav__menuitem--icon icon-sakai--sakai-samigo")
    if assign_div != None:
      assign_url = assign_div.parent.get('href')
      new_subject["assign_url"].iloc[index] = assign_url+"?criteria=assignment_status&panel=Main&sakai_action=doSort"
    if test_div != None:
      test_url = test_div.parent.get('href')
      new_subject["test_url"].iloc[index] = test_url
  return new_subject

def get_yet_assign(subject, session, loop):
  assign = pd.DataFrame(columns=["subject", "title", "deadline", "status", "url"])
  task = loop.run_until_complete(run(loop, session, subject.assign_url))
  for index, html in enumerate(task):
    # html = session.get(col.assign_url+"?criteria=assignment_status&panel=Main&sakai_action=doSort")
    bs = BeautifulSoup(html.text, 'html.parser')
    table = bs.find('table',class_="table table-hover table-striped table-bordered" )
    if bool(table):
      due = table.find_all('td', headers="status")
      for t in due:
        status = t.get_text().replace('\t','').replace('\n', '')
        if not (str(status[0:4]) == r"提出日時"):
          title = t.parent.find('td', headers="title").get_text().replace('\t','').replace('\n', '')
          until = t.parent.find('td', headers="dueDate").get_text().replace('\t','').replace('\n', '')
          assign = assign.append({'subject':subject.iloc[index].title, 'title':title, 'deadline':until, 'status':status, 'url':subject.iloc[index].assign_url}, ignore_index=True)

      # due.reverse() 逆ソート しなくても大丈夫かも
      # for t in due:
      #   status = t.get_text().replace('\t','').replace('\n', '')
      #   if str(status[0:4]) == r"提出日時":
      #     break
      #   title = t.parent.find('td', headers="title").get_text().replace('\t','').replace('\n', '')
      #   until = t.parent.find('td', headers="dueDate").get_text().replace('\t','').replace('\n', '')
      #   assign = assign.append({'subject':subject.iloc[index].title, 'title':title, 'deadline':until, 'status':status, 'url':subject.iloc[index].assign_url}, ignore_index=True)

  return assign

def get_yet_test(subject, session, loop):
  test = pd.DataFrame(columns=["subject", "title", "deadline"])
  task = loop.run_until_complete(run(loop, session, subject.query('test_url != ""').test_url))
  for index, html in enumerate(task):
    bs = BeautifulSoup(html.text, 'html.parser')
    table = bs.find('tbody',id="selectIndexForm:selectTabl:tbody_element")
    if table != None:
      test = test.append({'subject':subject.query('test_url != ""').iloc[index].title, 'title':table.find('span', class_="spanValue").text, 'deadline':table.find_all('td')[-1].text}, ignore_index=True)
  return test