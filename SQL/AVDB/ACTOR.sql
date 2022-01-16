-- DROP TABLE IF EXISTS `ACTOR`
CREATE TABLE `ACTOR`
(
	`actor_no`			INT NOT NULL AUTO_INCREMENT COMMENT '배우 고유번호'
	, `member_no`		INT NOT NULL COMMENT '등록자 고유번호 (FK: MEMBER.member_no)'
	, `actor_name`		VARCHAR(100) NOT NULL COMMENT '배우 이름' COLLATE 'utf8_general_ci'
	, `gender`			TINYINT NOT NULL DEFAULT (0) COMMENT '성별 ; 0=남, 1=여, 2=CD, 3=TS'
	, `height`			SMALLINT NULL COMMENT '키'
	, `weight`			TINYINT NULL COMMENT '몸무게'
	, `figure`			VARCHAR(100) NULL COMMENT '신체 정보 : 몸매 : B / W / H' COLLATE 'utf8_general_ci'
	, `cup_size`		VARCHAR(100) NULL COMMENT '신체 정보 : 컵사이즈' COLLATE 'utf8_general_ci'
	, `birth`			DATETIME NULL COMMENT '생년월일'
	, `debut_date`		DATE NULL COMMENT '첫 출연일'
	, `retire_date`		DATE NULL COMMENT '은퇴일'
	, `actor_detail`	MEDIUMTEXT NULL COMMENT '배우에 대한 상세 설명' COLLATE 'utf8_general_ci'
	, `reg_date`		DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP() COMMENT '배우 정보 등록시각'

	, PRIMARY KEY (`actor_no`) USING BTREE
)
COMMENT='배우 기본 정보 테이블'
COLLATE='utf8_general_ci'
ENGINE=InnoDB
;
