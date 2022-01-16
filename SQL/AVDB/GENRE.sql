-- DROP TABLE IF EXISTS `GENRE`
CREATE TABLE `GENRE`
(
	`genre_no`			INT NOT NULL AUTO_INCREMENT COMMENT '장르 고유번호'
	, `genre_name`		VARCHAR(100) NOT NULL COMMENT '장르 한글 이름' COLLATE 'utf8_general_ci'
	, `genre_descript`	MEDIUMTEXT NULL COMMENT '장르에 대한 상세 설명' COLLATE 'utf8_general_ci'
	, `reg_date`		DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP() COMMENT '언어 정보 등록시각'

	, PRIMARY KEY (`genre_no`) USING BTREE
)
COMMENT='장르 정보 테이블'
COLLATE='utf8_general_ci'
ENGINE=InnoDB
;
