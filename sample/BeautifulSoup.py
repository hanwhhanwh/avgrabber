import urllib.request, urllib.parse, urllib.error
from bs4 import BeautifulSoup



""" 주어진 문자열 lsit에서 순서에 맞게 값을 찾으면, key 항목에 값을 할당합니다.
"""
def findValue(strings, nIndex, avInfo, key):
	for nValueIndex in range(nIndex + 1, len(strings) - 1):
		if (strings[nValueIndex].strip() == ''):
			continue
		if (strings[nValueIndex].find(':') >= 0):
			return ''
		avInfo[key] = strings[nValueIndex]
	return ''


""" 주어진 문자열 lsit에서 순서에 맞게 모든 값들을 찾아서, 해당 key list에 추가합니다.
"""
def findValues(strings, nIndex, avInfo, key):
	values = []
	for nValueIndex in range(nIndex + 1, len(strings) - 1):
		if (strings[nValueIndex].strip() == ''):
			continue
		if (strings[nValueIndex].find(':') >= 0):
			break
		if (strings[nValueIndex].find('出演者') >= 0):
			break
		values.append(strings[nValueIndex])
	if (len(values) > 0):
		avInfo[key] = values
	return ''



good_num = 'SNIS-832'

# headerUserAgent = 'user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36 Edg/85.0.564.63'

url = 'https://www.javbus.com/ja/' + good_num
req = urllib.request.Request(
    url, 
    data = None, 
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
    }
)

handler = urllib.request.urlopen(req)
html = handler.read()
# html = urllib.request.urlopen(url).read()
bs = BeautifulSoup(html, 'html.parser')

# class='col-md-3 info' 인 DIV 태그 찾기
divAvInfo = bs.find('div', attrs={'class': 'col-md-3 info'})
strings = list(divAvInfo.strings)
print(strings)

# print(strings[1])

# initialize AV Info dictionary
avInfo = {}

nStringCount = len(strings)
for nIndex in range(0, nStringCount - 1):
	item_name = strings[nIndex]
	if (item_name == '品番:'):
		findValue(strings, nIndex, avInfo, 'good_num')
	if (item_name == '発売日:'):
		findValue(strings, nIndex, avInfo, 'publish_date')
	if (item_name == '収録時間:'):
		findValue(strings, nIndex, avInfo, 'play_time')
	if (item_name == '監督:'):
		findValue(strings, nIndex, avInfo, 'director')
	if (item_name == 'メーカー:'):
		findValue(strings, nIndex, avInfo, 'maker')
	if (item_name == 'レーベル:'):
		findValue(strings, nIndex, avInfo, 'label')
	if (item_name == 'シリーズ:'):
		findValue(strings, nIndex, avInfo, 'series')
	if (item_name == 'ジャンル:'):
		findValues(strings, nIndex, avInfo, 'genre')
	if (item_name == '出演者'):
		findValues(strings, nIndex + 1, avInfo, 'actress')

print(avInfo)


# bs = BeautifulSoup(divAvInfo, 'html.parser')

# tags = bs.find('p')
# for tag in tags :
# 	print(tag)