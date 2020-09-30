import urllib.request, urllib.parse, urllib.error
from bs4 import BeautifulSoup

url = 'https://www.naver.com'
html = urllib.request.urlopen(url).read()
bs = BeautifulSoup(html, 'html.parser')

# 모든 A 태그의 href 속성만 모아 출력하기
tags = bs('a')
for tag in tags:
	print(tag.get('href', None))
