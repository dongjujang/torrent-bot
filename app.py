#-*- coding: utf-8 -*-
import os
import json
import time
import requests
import BeautifulSoup

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.93 Safari/537.36'
LATEST_NUMBERS = {}

def post_message(title, link):
  webhook = os.environ.get('WEBHOOK', None)
  if not webhook:
    return
  payload = { 'text': '<' + link + '|' + title + '>' }
  data = { 'payload': json.dumps(payload) }
  try:
    requests.post(url, data=data)
  except Exception as e:
    print e

def get_posts(url):
  headers = { 'User-Agent': USER_AGENT }
  response = None
  try:
    response = requests.get(url, headers=headers)
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
    latest_number = LATEST_NUMBERS.get(url, 0)
    if number <= latest_number:
      continue

    LATEST_NUMBERS[url] = number
    wr_id = link.split('wr_id=')[1]
    link = url + '&wr_id=' + wr_id
    #link = link.replace('board.php', 'download.php')

    post_message(title, link)

def main():
  while True:

    for zero in '.':
      torrent_urls = os.environ.get('URLS', None)
      if torrent_urls == None:
        break
      for url in torrent_urls.split(','):
        get_posts(url)

    time.sleep(1)
    #time.sleep(60 * 5)
        
if __name__ == '__main__':
  main()
