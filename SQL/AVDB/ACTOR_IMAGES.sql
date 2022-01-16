-- DROP TABLE IF EXISTS `ACTOR_IMAGES`
CREATE TABLE `ACTOR_IMAGES`
(	
	`actor_image_no`		INT NOT NULL AUTO_INCREMENT COMMENT '배우 이미지 고유번호'
	, `actor_no`			INT NOT NULL COMMENT '배우 고유번호 (FK: ACTOR.actor_no)'
	, `actor_image_url`		VARCHAR(255) NOT NULL COMMENT '배우 이미지 주소 정보' COLLATE 'utf8_general_ci'
	, `width`				SMALLINT NULL COMMENT '이미지 폭'
	, `height`				SMALLINT NULL COMMENT '이미지 높이'
	, `reg_date`			DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP() COMMENT '배우 이미지 정보 등록시각'

	, PRIMARY KEY (`actor_image_no`) USING BTREE
)
COMMENT='배우에 대한 이미지 정보 테이블'
COLLATE='utf8_general_ci'
ENGINE=InnoDB
;
