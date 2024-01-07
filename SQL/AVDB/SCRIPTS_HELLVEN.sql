-- DROP TABLE IF EXISTS `SCRIPTS_HELLVEN`
CREATE TABLE IF NOT EXISTS `SCRIPTS_HELLVEN`
(
	`script_hellven_no`		INT NOT NULL AUTO_INCREMENT COMMENT 'HELLVEN 자막 파일 고유번호'
	, `hellven_board_no`	INT NOT NULL COMMENT 'HELLVEN 자막 게시판의 번호'
	, `title`				VARCHAR(200) NULL COMMENT '자막 파일 제목 (배우 이름)' COLLATE 'utf8mb4_unicode_ci'
	, `film_id`				VARCHAR(50) NULL COMMENT '작품의 품번 (FK: FILM.film_id)'
	, `board_date`			DATETIME NOT NULL COMMENT '자막 등록 날짜'
	, `category`			CHAR(1) NOT NULL DEFAULT ('J') COMMENT '자막 구분: "J"=일본, "W"=서양, "C"=중국, "E"=기타, "A"=A.I 자막'
	, `script_name`			VARCHAR(200) NOT NULL COMMENT '자막 파일 이름' COLLATE 'utf8mb4_unicode_ci'
	, `file_size`			VARCHAR(50) NULL COMMENT '스크립트 파일 크기' COLLATE 'utf8mb4_unicode_ci'
	, `cover_image_url`		VARCHAR(255) NULL COMMENT '표지 이미지 주소 정보' COLLATE 'utf8mb4_unicode_ci'
	, `film_no`				INT NULL COMMENT '영상 고유 번호 (FK: FILM.film_no)'
	, `tags`				VARCHAR(250) NOT NULL COMMENT '태그 문자열' COLLATE 'utf8mb4_unicode_ci'
	, `content`				TEXT NOT NULL COMMENT '내용' COLLATE 'utf8mb4_unicode_ci'
	, `reg_date`			DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP() COMMENT '정보 등록시각'

	, PRIMARY KEY (`script_hellven_no`) USING BTREE
	, UNIQUE INDEX `UK_FILM_ID_FILE_SIZE` (`hellven_board_no`) USING BTREE
	, INDEX `IX_FILM_ID` ( `film_id` ) USING BTREE
)
COMMENT='HELLVEN 자막 정보 관리 테이블'
COLLATE='utf8mb4_unicode_ci'
ENGINE=InnoDB
;

/*
ALTER TABLE `SCRIPTS_HELLVEN`
	ADD INDEX `IX_FILM_ID` ( `film_id` ) USING BTREE;
*/