-- PYTHON_DEMO 데이터베이스 및 관련 계정 (python) 생성
CREATE DATABASE IF NOT EXISTS `PYTHON_DEMO` /*!40100 DEFAULT CHARACTER SET utf8 */;

CREATE USER 'python'@'%' IDENTIFIED BY 'python2@2@';
GRANT ALL PRIVILEGES ON `PYTHON_DEMO`.* TO 'python'@'%' WITH GRANT OPTION;
FLUSH PRIVILEGES;

/*
-- PYTHON_DEMO 데이터베이스 및 관련 계정 (python) 삭제
REVOKE ALL PRIVILEGES ON `PYTHON_DEMO`.* FROM 'python'@'%';
DROP USER 'python'@'%';
DROP DATABASE `PYTHON_DEMO`;

*/


CREATE TABLE IF NOT EXISTS MEMBER
(
	member_no	INT NOT NULL AUTO_INCREMENT COMMENT 'member number'
	, member_name VARCHAR (100) NOT NULL COMMENT 'member name'

	, PRIMARY KEY ( member_no )
)
COMMENT 'Member Table'
COLLATE='utf8_general_ci'
ENGINE=InnoDB
;



INSERT INTO member ( member_name ) VALUES ( 'DEMO1' ), ( 'DEMO2' );