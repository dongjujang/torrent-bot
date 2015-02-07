#-*- coding: utf-8 -*-
import os
import json
import time
import redis
import urllib
import requests
import BeautifulSoup

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.93 Safari/537.36'
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', '')
DB = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0, password=REDIS_PASSWORD)

def post_message(title, link):
  webhook = os.environ.get('WEBHOOK', None)
  if not webhook:
    return
  payload = { 'text': '<' + link + '|' + title + '>' }
  data = { 'payload': json.dumps(payload) }
  try:
    requests.post(webhook, data=data)
  except Exception as e:
    print e

def get_torrent_url(session, headers, download_url):
  new_url = None
  index = 0
  while True:
    try:
      new_url = ("%s&no=%s" % (download_url, index))
      response = session.get(new_url, headers=headers, stream=True)
      if not response.ok:
        break
      content_disposition = response.headers.get('content-disposition', '')
      if not '.torrent' in content_disposition:
        index += 1
        continue
      break
    except Exception as e:
      print e
      break

  return new_url

def get_posts(url):
  session = requests.Session()
  headers = { 'User-Agent': USER_AGENT, 'referer': url }
  response = None
  try:
    response = session.get(url, headers=headers)
  except Exception as e:
    print e
  soup = BeautifulSoup.BeautifulSoup(response.text)
  board_list = soup.find('table', attrs={'id': 'board_list'})
  
  if not board_list:
    return
  elements = board_list.findAll('tr')
  if not elements:
    return
  
  index = len(elements)
  while True:
    index -= 1
    if index < 0:
      break
    element = elements[index]
    num_td = element.find('td', attrs={'class': 'num'})
    subject_td = element.find('td', attrs={'class': 'subject'})
    if not num_td or not subject_td:
      continue

    num_span = num_td.find('span')
    subject_a = subject_td.find('a')
    if not num_span or not subject_a:
      continue

    number = int(num_span.text)
    title = subject_a.text
    link = subject_a.get('href', None)
    latest_number = None
    try:
      latest_number = DB.get(url)
      if latest_number == None:
        latest_number = 0
      else:
        latest_number = int(latest_number)
    except Exception as e:
      print e
      continue

    if number <= latest_number:
      continue

    try:
      DB.set(url, number)
    except Exception as e:
      print e
      continue
    wr_id = link.split('wr_id=')[1]
    link = url + '&wr_id=' + wr_id
    proxy_url = os.environ.get('PROXY_URL', None)
    if proxy_url:
      download_url = link.replace('board.php', 'download.php')
      download_url = get_torrent_url(session, headers, download_url)
      if not download_url:
        continue
      referer = link
      params = { 'referer': referer, 'download_url': download_url }
      link = proxy_url + '?' + urllib.urlencode(params)

    post_message(title, link)

def main():
  while True:

    for zero in '.':
      torrent_urls = os.environ.get('URLS', None)
      if torrent_urls == None:
        break
      for url in torrent_urls.split(','):
        get_posts(url)

    time.sleep(60 * 10)
        
if __name__ == '__main__':
  main()
