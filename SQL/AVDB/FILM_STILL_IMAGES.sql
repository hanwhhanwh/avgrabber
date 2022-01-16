-- DROP TABLE IF EXISTS `FILM_STILL_IMAGES`
CREATE TABLE `FILM_STILL_IMAGES`
(
	`film_still_image_no`		INT NOT NULL AUTO_INCREMENT COMMENT '작품 스틸 이미지 고유번호'
	, `film_no`					INT NOT NULL COMMENT '작품 고유번호 (FK: FILM.film_no)'
	, `still_image_url`			VARCHAR(255) NOT NULL COMMENT '작품 스틸 이미지 주소 정보' COLLATE 'utf8_general_ci'
	, `still_image_thumb_url`	VARCHAR(255) NOT NULL COMMENT '썸브용 작품 스틸 이미지 주소 정보' COLLATE 'utf8_general_ci'
	, `width`					SMALLINT NULL COMMENT '이미지 폭'
	, `height`					SMALLINT NULL COMMENT '이미지 높이'

	, PRIMARY KEY (`film_still_image_no`) USING BTREE
	, INDEX IX_FILM_NO (`film_no`)
)
COMMENT='작품 스틸 이미지 정보 테이블'
COLLATE='utf8_general_ci'
ENGINE=InnoDB
;