-- DROP TABLE IF EXISTS `COMMENTS`
CREATE TABLE `COMMENTS`
(
	`comment_no`			INT NOT NULL AUTO_INCREMENT COMMENT '댓글/감상 고유번호'
	, `film_no`				INT NOT NULL COMMENT '작품 고유번호 (FK: FILM.film_no)'
	, `member_no`			INT NOT NULL COMMENT '작성자 고유번호 (FK: MEMBER.member_no)'
	, `film_rate`			TINYINT NULL COMMENT '작품에 대한 평점(0 ~ 100)' COLLATE 'utf8_general_ci'
	, `film_comment`		MEDIUMTEXT NULL COMMENT '작품에 대한 댓글/감상' COLLATE 'utf8_general_ci'
	, `reg_date`			DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP() COMMENT '댓글/감상 정보 등록시각'

	, PRIMARY KEY (`comment_no`) USING BTREE
)
COMMENT='작품에 대한 댓글/감상 정보 테이블'
COLLATE='utf8_general_ci'
ENGINE=InnoDB
;
