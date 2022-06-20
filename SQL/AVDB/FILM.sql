-- DROP TABLE IF EXISTS `FILM`
CREATE TABLE `FILM`
(
	`film_no`				INT NOT NULL AUTO_INCREMENT COMMENT '작품 고유번호'
	, `member_no`			INT NOT NULL COMMENT '작성자 고유번호 (FK: MEMBER.member_no)'
	, `film_id`				VARCHAR(50) NOT NULL COMMENT '작품의 품번' COLLATE 'utf8_general_ci'
	, `product_company_no`	INT NULL COMMENT '제작사 고유번호 (FK: PRODUCT_COMPANY.product_company_no)'
	, `label_no`			INT NULL COMMENT '레이블 고유번호 (FK: LABEL.label_no)'
	, `film_kr_name`		VARCHAR(255) NULL COMMENT '작품의 한글 제목' COLLATE 'utf8_general_ci'
	, `film_en_name`		VARCHAR(255) NULL COMMENT '작품의 영문 제목' COLLATE 'utf8_general_ci'
	, `film_jp_name`		VARCHAR(255) NULL COMMENT '작품의 일문 제목' COLLATE 'utf8_general_ci'
	, `film_ch_name`		VARCHAR(255) NULL COMMENT '작품의 중문 제목' COLLATE 'utf8_general_ci'
	, `length`				SMALLINT NULL COMMENT '시간 (분)'
	, `cover_image_url`		VARCHAR(255) NULL COMMENT '표지 이미지 주소 정보' COLLATE 'utf8_general_ci'
	, `publish_date`		DATE NULL COMMENT '작품 출시일'
	, `film_stroy`			MEDIUMTEXT NULL COMMENT '작품 줄거리' COLLATE 'utf8_general_ci'
	, `reg_date`			DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP() COMMENT '작품 정보 등록시각'

	, PRIMARY KEY (`film_no`) USING BTREE
	, UNIQUE INDEX `UK_FILM_ID` (`film_id`) USING BTREE
)
COMMENT='작품 기본 정보 테이블'
COLLATE='utf8_general_ci'
ENGINE=InnoDB
;
