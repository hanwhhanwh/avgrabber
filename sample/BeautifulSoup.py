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

# DIV class='col-md-9 screencap' ; 표지 이미지 및 제목
"""
<div class="col-md-9 screencap">
            <a class="bigImage" href="/pics/cover/8iwe_b.jpg"><img src="/pics/cover/8iwe_b.jpg" title="女体化した俺は親友に求められるがまま、受け入れて、心も女になっていた。 川上奈々美"></a>
        </div>"""
divAvTitle = bs.find('div', attrs={'class': 'col-md-9 screencap'})


# class='col-md-3 info' 인 DIV 태그 찾기 ; 작품 상세 정보
"""<div class="col-md-3 info">
            <p><span class="header">品番:</span> <span style="color:#CC0000;">DASD-933</span>
            </p>
            <p><span class="header">発売日:</span> 2021-11-05</p>
            <p><span class="header">収録時間:</span> 120分</p>
                        <p><span class="header">監督:</span> <a href="https://www.javbus.com/ja/director/ay">三島六三郎</a></p>
                                    <p><span class="header">メーカー:</span> <a href="https://www.javbus.com/ja/studio/a5">ダスッ！</a>
            </p>                        <p><span class="header">レーベル:</span> <a href="https://www.javbus.com/ja/label/fn">ダスッ！</a>
            </p>                        <p><span class="header">シリーズ:</span> <a href="https://www.javbus.com/ja/series/uhk">女体化した俺は親友に求められるがまま、受け入れて、心も女になっていた。</a>
            </p>            <p class="header">ジャンル:<span id="genre-toggle" class="glyphicon glyphicon-plus" style="cursor: pointer;"></span></p>
            <p>            <span class="genre"><label><input type="checkbox" name="gr_sel" value="4o"><a href="https://www.javbus.com/ja/genre/4o">ハイビジョン</a></label></span>
                        <span class="genre"><label><input type="checkbox" name="gr_sel" value="g"><a href="https://www.javbus.com/ja/genre/g">独占配信</a></label></span>
                        <span class="genre"><label><input type="checkbox" name="gr_sel" value="f"><a href="https://www.javbus.com/ja/genre/f">単体作品</a></label></span>
                        <span class="genre"><label><input type="checkbox" name="gr_sel" value="4u"><a href="https://www.javbus.com/ja/genre/4u">ドラマ</a></label></span>
                        <span class="genre"><label><input type="checkbox" name="gr_sel" value="1f"><a href="https://www.javbus.com/ja/genre/1f">スレンダー</a></label></span>
                        <span class="genre"><label><input type="checkbox" name="gr_sel" value="4"><a href="https://www.javbus.com/ja/genre/4">中出し</a></label></span>
                        <span class="genre"><label><input type="checkbox" name="gr_sel" value="80"><a href="https://www.javbus.com/ja/genre/80">性転換・女体化</a></label></span>
            <span class="genre"><button id="gr_btn" type="button" class="btn">多重提出する</button></span>
            </p>            <p class="star-show"><span class="header" style="cursor: pointer;">出演者</span>:<span id="star-toggle" class="glyphicon glyphicon-plus" style="cursor: pointer;"></span></p>
                
                <ul>
                                      <div id="star_82r" class="star-box star-box-common star-box-up idol-box">
                      <li>
                          <a href="https://www.javbus.com/ja/star/82r"><img src="/pics/actress/82r_a.jpg" title="川上奈々美"></a>
                          <div class="star-name"><a href="https://www.javbus.com/ja/star/82r" title="川上奈々美">川上奈々美</a></div>
                      </li>
                    </div>
                                  </ul>  
                
			<p>
						<span class="genre" onmouseover="hoverdiv(event,'star_82r')" onmouseout="hoverdiv(event,'star_82r')">
					<a href="https://www.javbus.com/ja/star/82r">川上奈々美</a>
				</span>
                					</p>
        </div>
"""
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


# DIV id='sample-waterfall' ; 작품 스틸 이미지
divSampleImages = bs.find('div', attrs={'id': 'sample-waterfall'})
for a in divSampleImages.select('a'):
	print('still_images = ' + a['href'])
	img = a.find('img')
	if (img != None):
		print('  thumb = ' + img['src'])

# bs = BeautifulSoup(divAvInfo, 'html.parser')

# tags = bs.find('p')
# for tag in tags :
# 	print(tag)