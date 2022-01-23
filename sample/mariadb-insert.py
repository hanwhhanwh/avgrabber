# author : hbesthee@naver.com
# date : 2022-01-23

from sqlalchemy import create_engine
from typing import Final


# DATABASE Configuration
DDB_HOST				: Final = "127.0.0.1"
DDB_PORT				: Final = "23306"
DDB_USER_ID				: Final = "avdbuser"
DDB_PASSWORD			: Final = "%40!avdb~user"
DDB_DATABASE			: Final = "AVDB"

DB_URL					: Final = f"mysql+mysqlconnector://{DDB_USER_ID}:{DDB_PASSWORD}@{DDB_HOST}:{DDB_PORT}/{DDB_DATABASE}?charset=utf8"


def connect_database():
	""" Database 연결을 위한 engine을 생성하여 반환합니다. """
	database = create_engine(DB_URL, encoding = 'utf-8')
	return database


class AvgrabberBaseModel(object):
	""" 데이터베이스 모델의 기본 클래스 
		데이터 모델은 본 클래스를 상속받아 간단하게 처리하기
	"""

	engine = None
	db_url = None
	encoding = 'utf-8'
	connection = None
	cursor = None


	def __init__(self, db_url, encoding = 'utf-8'):
		""" 클래스 생성자
			db_url : 데이터베이스 연결 문자열. sqlalchemy에서 인식 가능한 문자열이어야 함
			encoding : 데이터베이스 인코딩 설정
		"""
		self.db_url = db_url
		self.encoding = encoding


	def get_engine(self):
		""" sqlalchemy에서 연결 문자열로 생성한 데이터베이스 연결을 위한 엔진 객체 """
		self.engine = create_engine(self.db_url, encoding = self.encoding)
		return self.engine


	def connect_database(self):
		engine = self.get_engine()
		if engine == None:
			# 데이터베이스 연결을 위한 엔진 객체 얻기 실패
			return None, None, { 'code':500, 'message': 'database engine fail!' }
		try:
			self.connection = engine.raw_connection()
		except Exception as e: # 데이터베이스 연결 실패
			return None, None, { 'code':500, 'message': f'database connection fail! >> {e}' }

		try:
			self.cursor = self.connection.cursor()  # get Database cursor
		except Exception as e: # Database cursor fail
			return None, None, { 'code':500, 'message': f'database cursor fail! >> {e}' }

		return self.connection, self.cursor, None


avdb_model = AvgrabberBaseModel(DB_URL)
connection, cursor, result = avdb_model.connect_database()
if result != None:
	print(result) # 데이터베이스 연결시 오류 발생

query = """
INSERT INTO LANG (`lang_no`, `kr_name`, `en_name`, `jp_name`, `ch_name`)
VALUES (1, '한국어', 'Korean', '韓國語', '韓國語')
, (2, '영어', 'English', '美國', '美國')
, (3, '일본어', 'Japan', '日本語', '日本語')
, (4, '중국어', 'China', '中國語', '中國語')
;
"""

cursor.execute(query, )
connection.commit()