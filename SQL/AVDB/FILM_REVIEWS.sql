-- DROP TABLE IF EXISTS `FILM_REVIEWS`
CREATE TABLE `FILM_REVIEWS`
(
	`film_no`				INT NOT NULL AUTO_INCREMENT COMMENT '작품 고유번호'
	, `member_no`			INT NOT NULL COMMENT '장르 고유번호 (FK: GENRE.member_no)'
	, `film_rate`			TINYINT NULL COMMENT '작품에 대한 점수 (100점 만점 기준)'
	, `film_review`			VARCHAR(2000) NULL COMMENT '작품 한줄평' COLLATE 'utf8_general_ci'
	, `reg_date`			DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP() COMMENT '작품 정보 등록시각'

	, PRIMARY KEY (`film_no`, `member_no`) USING BTREE
)
COMMENT='작품 장르 정보 테이블'
COLLATE='utf8_general_ci'
ENGINE=InnoDB
;
