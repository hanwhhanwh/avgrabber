-- DROP TABLE IF EXISTS `FILM_ACTORS`
CREATE TABLE `FILM_ACTORS`
(
	`film_no`			INT NOT NULL AUTO_INCREMENT COMMENT '작품 고유번호'
	, `actor_no`		INT NOT NULL COMMENT '배우 고유번호 (FK: ACTOR.actor_no)'

	, PRIMARY KEY (`film_no`, `actor_no`) USING BTREE
)
COMMENT='작품 장르 정보 테이블'
COLLATE='utf8_general_ci'
ENGINE=InnoDB
;
