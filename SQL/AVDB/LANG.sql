-- DROP TABLE IF EXISTS `LANG`
CREATE TABLE `LANG`
(
	`lang_no`			INT NOT NULL AUTO_INCREMENT COMMENT '언어 고유번호'
	, `kr_name`			VARCHAR(100) NOT NULL COMMENT '언어 한글 이름' COLLATE 'utf8_general_ci'
	, `en_name`			VARCHAR(100) NOT NULL COMMENT '언어 영문 이름' COLLATE 'utf8_general_ci'
	, `jp_name`			VARCHAR(100) NULL COMMENT '언어 일문 이름' COLLATE 'utf8_general_ci'
	, `ch_name`			VARCHAR(100) NULL COMMENT '언어 중문 이름' COLLATE 'utf8_general_ci'
	, `reg_date`		DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP() COMMENT '언어 정보 등록시각'

	, PRIMARY KEY (`lang_no`) USING BTREE
)
COMMENT='언어 정보 테이블'
COLLATE='utf8_general_ci'
ENGINE=InnoDB
;