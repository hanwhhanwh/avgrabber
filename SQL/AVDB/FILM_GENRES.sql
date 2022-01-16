-- DROP TABLE IF EXISTS `FILM_GENRES`
CREATE TABLE `FILM_GENRES`
(
	`film_no`			INT NOT NULL AUTO_INCREMENT COMMENT '작품 고유번호'
	, `genre_no`		INT NOT NULL COMMENT '장르 고유번호 (FK: GENRE.genre_no)'

	, PRIMARY KEY (`film_no`, `genre_no`) USING BTREE
)
COMMENT='작품 장르 정보 테이블'
COLLATE='utf8_general_ci'
ENGINE=InnoDB
;
