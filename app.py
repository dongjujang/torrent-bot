

#-*- coding: utf-8 -*-
import os
import json
import time
import bottle
import urllib
import requests
import threading
import BeautifulSoup

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.93 Safari/537.36'
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', None)

collection = 'movie_eng'

keys = ['subject',
        'torrent_file',
        'smi_file',
        'size',
        'number']

doc = {}

def post_message(doc):
  if not WEBHOOK_URL:
    print('No webhook url!')
    return
  requests.post(WEBHOOK_URL + '/' + collection, data=doc)
  print(doc)

def get_torrent_url(session, headers, referer, download_url, page):
  new_url = None
  torrent_url = None
  smi_url = None

  try:
    response = session.get(referer, headers=headers)
    if not response.ok:
      return new_url
  except Exception as e:
    print e
    return new_url

  headers['referer'] = referer
  index = 0
  while True:
    try:
      new_url = ("%s&no=%s&%s" % (download_url, index, page))
      response = session.get(new_url, headers=headers, stream=True)
      if not response.ok:
        break
      content_disposition = response.headers.get('content-disposition', '')
      if '.torrent' in content_disposition:
        torrent_url = new_url
      if '.smi' in content_disposition:
        smi_url = new_url
      if torrent_url and smi_url:
        break
      index += 1
      if index > 4:
        smi_url = 'nosub'
        break
      
      
    except Exception as e:
      print e
      break

#  torrent_smi_url = torrent_url + 'preamble' + smi_url
  torrent_smi_url = torrent_url + 'preamble{}'.format(smi_url)
  print torrent_smi_url
  return torrent_smi_url


def get_posts(url, url_no_page):
  session = requests.Session()
  headers = { 'User-Agent': USER_AGENT, 'referer': url }
  response = None
  try:
    response = session.get(url, headers=headers)
  except Exception as e:
    print e
  soup = BeautifulSoup.BeautifulSoup(response.text)
  board_list = soup.find('table', attrs={'class': 'board_list'})

  if not board_list:
    return
  elements = board_list.findAll('tr')
  if not elements:
    return
  for element in elements:
#    print(element)
    subject_td = element.find('td', attrs={'class': 'subject'})
    size_td = element.find('td', attrs={'class': 'size'})

    if subject_td != None:      
      subject_a = subject_td.find('a')

      size = size_td.text
      doc[keys[3]] = size
      title = subject_a.text
      doc[keys[0]] = title
      link = subject_a.get('href', None)

      wr_id_temp = link.split('wr_id=')[1]
      wr_id = wr_id_temp.split('&')[0]
      page = wr_id_temp.split('&')[1]
      number = int(wr_id)
      doc[keys[4]] = number
#      print(size, title, number)
      link = url_no_page + '&wr_id=' + wr_id
      proxy_url = os.environ.get('PROXY_URL', None)
      if proxy_url:
        referer = link + '&' + page
        download_url_replace = referer.replace('board.php', 'download.php')
        download_url = get_torrent_url(session, headers, referer, download_url_replace, page)
        if not download_url:
          continue
        torrent_file_url = download_url.split('preamble')[0]
        smi_file_url = download_url.split('preamble')[1]
        
        params = { 'referer': referer, 'download_url': torrent_file_url }
        torrent_file_link = proxy_url + '?' + urllib.urlencode(params)

        params_smi = { 'referer': referer, 'download_url': smi_file_url }
        smi_file_link = proxy_url + '?' + urllib.urlencode(params_smi)
        if smi_file_url == 'nosub':
          smi_file_link = 'nosub'

        doc[keys[1]] = torrent_file_link
        doc[keys[2]] = smi_file_link
        
      post_message(doc)

def main():

      torrent_urls = os.environ.get('TORRENT_URLS', None)
      if torrent_urls == None:
        print("No torrent_url")
        return
      while True:
        for url in torrent_urls.split(','):
          num = 1318
          page_num = range(1, num + 1)
          for i in page_num:
            get_posts(url + '&page=' + str(num), url)
            num = num - 1
          
            time.sleep(30)
        
@bottle.route('/')
def index():
  return ''

if __name__ == '__main__':
  debug = False
  if debug:
    main()
  else:
    threading.Thread(target=main).start()
    port = os.environ.get('PORT', 8888)
    bottle.run(host='0.0.0.0', port=port)
