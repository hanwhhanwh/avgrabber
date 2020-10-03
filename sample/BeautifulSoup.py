import urllib.request, urllib.parse, urllib.error
from bs4 import BeautifulSoup


def findValue(strings, nIndex):
	for nValueIndex in range(nIndex + 1, len(strings) - 1):
		if (strings[nValueIndex].strip() == ''):
			continue
		if (strings[nValueIndex].find(':') >= 0):
			return ''
		return strings[nValueIndex]
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

avInfo = {}
avInfo['genre'] = []
avInfo['actress'] = []

nStringCount = len(strings)
for nIndex in range(0, nStringCount - 1):
	value = strings[nIndex]
	if (value == '品番:'):
		avInfo['good_num'] = findValue(strings, nIndex)
	if (value == '発売日:'):
		avInfo['publish_date'] = findValue(strings, nIndex)
	if (value == '収録時間:'):
		avInfo['play_time'] = findValue(strings, nIndex)
	if (value == '監督:'):
		avInfo['director'] = findValue(strings, nIndex)
	if (value == 'メーカー:'):
		avInfo['maker'] = findValue(strings, nIndex)
	if (value == 'レーベル:'):
		avInfo['label'] = findValue(strings, nIndex)
	if (value == 'シリーズ:'):
		avInfo['series'] = findValue(strings, nIndex)
	if (value == 'ジャンル:'):
		avInfo['genre'].append(findValue(strings, nIndex))
	if (value == '出演者'):
		avInfo['actress'].append(findValue(strings, nIndex + 1))

print(avInfo)


# bs = BeautifulSoup(divAvInfo, 'html.parser')

# tags = bs.find('p')
# for tag in tags :
# 	print(tag)