-- DROP TABLE IF EXISTS `MEMBER`
CREATE TABLE IF NOT EXISTS `MEMBER`
(
	`member_no`			INT NOT NULL AUTO_INCREMENT COMMENT '회원 고유번호'
	, `member_id`		VARCHAR(50) NOT NULL COMMENT '회원 ID ' COLLATE 'utf8_general_ci'
	, `password`		VARBINARY(128) NULL DEFAULT NULL COMMENT '비밀번호'
	, `member_name`		VARCHAR(100) NOT NULL COMMENT '회원명' COLLATE 'utf8_general_ci'
	, `phone_no`		VARCHAR(20) NULL DEFAULT NULL COMMENT '휴대폰 번호' COLLATE 'utf8_general_ci'
	, `email`			VARCHAR(100) NULL DEFAULT NULL COMMENT '이메일' COLLATE 'utf8_general_ci'
	, `tel_no`			VARCHAR(20) NULL DEFAULT NULL COMMENT '전화번호' COLLATE 'utf8_general_ci'
	, `descript`		VARCHAR(250) NULL DEFAULT NULL COMMENT '회원 설명' COLLATE 'utf8_general_ci'
	, `zip_code`		VARCHAR(10) NULL DEFAULT NULL COMMENT '우편번호' COLLATE 'utf8_general_ci'
	, `address1`		VARCHAR(250) NULL DEFAULT NULL COMMENT '도로명 주소' COLLATE 'utf8_general_ci'
	, `address2`		VARCHAR(250) NULL DEFAULT NULL COMMENT '상세 주소' COLLATE 'utf8_general_ci'
	, `company_name`	VARCHAR(20) NOT NULL COMMENT '상호 / 회사명' COLLATE 'utf8_general_ci'
	, `ceo_name`		VARCHAR(50) NULL DEFAULT NULL COMMENT '대표자 성명' COLLATE 'utf8_general_ci'
	, `fax_no`			VARCHAR(20) NULL DEFAULT NULL COMMENT 'FAX 번호' COLLATE 'utf8_general_ci'
	, `logo_file_name`	VARCHAR(100) NULL DEFAULT NULL COMMENT '로고 파일 이름' COLLATE 'utf8_general_ci'
	, `is_agreement`	BIT(1) NOT NULL COMMENT '개인정보 수집 이용 동의' COLLATE 'utf8_general_ci'
	, `is_3rd`			BIT(1) NOT NULL COMMENT '개인정보 제3자 제공 동의' COLLATE 'utf8_general_ci'
	, `is_approved`		BIT(1) NOT NULL DEFAULT (1) COMMENT '회원가입 승인 여부' COLLATE 'utf8_general_ci'
	, `reg_date`		DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP() COMMENT '정보 등록시각'
	, PRIMARY KEY (`member_no`) USING BTREE
	, UNIQUE INDEX `UK_LOGIN_ID` (`member_id`) USING BTREE
)
COMMENT='회원 정보 테이블'
COLLATE='utf8_general_ci'
ENGINE=InnoDB
;
