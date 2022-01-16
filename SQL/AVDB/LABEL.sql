-- DROP TABLE IF EXISTS `LABEL`
CREATE TABLE `LABEL`
(
	`label_no`			INT NOT NULL AUTO_INCREMENT COMMENT '레이블 고유번호'
	, `kr_name`			VARCHAR(100) NOT NULL COMMENT '레이블 한글 이름' COLLATE 'utf8_general_ci'
	, `en_name`			VARCHAR(100) NOT NULL COMMENT '레이블 영문 이름' COLLATE 'utf8_general_ci'
	, `jp_name`			VARCHAR(100) NULL COMMENT '레이블 일문 이름' COLLATE 'utf8_general_ci'
	, `ch_name`			VARCHAR(100) NULL COMMENT '레이블 중문 이름' COLLATE 'utf8_general_ci'
	, `reg_date`		DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP() COMMENT '레이블 정보 등록시각'

	, PRIMARY KEY (`label_no`) USING BTREE
)
COMMENT='레이블 정보 테이블'
COLLATE='utf8_general_ci'
ENGINE=InnoDB
;
