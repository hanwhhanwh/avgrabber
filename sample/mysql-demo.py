import pymysql
 
# MySQL Connection 연결
conn = pymysql.connect(host='localhost', user='python', password='python2@2@',
						db='PYTHON_DEMO', charset='utf8')
 
# Connection 으로부터 Cursor 생성
curs = conn.cursor()
 
# 데이터 삽입 (INSERT)
sqlInsertMember = "INSERT INTO MEMBER ( member_name ) VALUES ('NEW MEMBER1');"
curs.execute(sqlInsertMember)

# SELECT 실행 예시
sqlSelectMember = "SELECT * FROM MEMBER"
curs.execute(sqlSelectMember)
 
# 레코드 Fetch
rows = curs.fetchall()
print(rows)     # 전체 rows
print(rows[0])  # 첫 번째 레코드 : (1, 'DEMO1')
print(rows[1])  # 두 번째 레코드 : (2, 'DEMO2')
print(rows[2])  # 세 번째 신규 레코드 : (3, 'NEW MEMBER1')

# Connection 닫기
conn.close()