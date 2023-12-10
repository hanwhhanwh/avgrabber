-- DROP TABLE IF EXISTS `FILM_FILE`
CREATE TABLE `FILM_FILE`
(
	`file_no`				INT NOT NULL AUTO_INCREMENT COMMENT 'FILM 파일 정보의 고유번호'
	, `film_no`				INT NOT NULL COMMENT 'FILM 고유번호 (FK: FILM.film_on)'
	, `file_name`			VARCHAR(800) NOT NULL COMMENT '파일 이름' COLLATE 'utf8mb4_unicode_ci'
	, `file_size`			INT64 NULL COMMENT COMMENT '파일 용량'
	, `lang`				VARCHAR(10) NOT NULL COMMENT '언어 ; KR, CH, US, ...'
	, `resolution`			CHAR(1) NOT NULL DEFAULT ('F') COMMENT '영상파일의 해상도 : F=FHD, H=HD, S=SD, 4=4K, 8=8K, ...'
	, `has_owned`			BIT NOT NULL DEFAULT (1) COMMENT '소유 여부'
	, `has_script`			BIT NOT NULL DEFAULT (1) COMMENT '자막 포함 여부'
	, `pixelated`			BIT NOT NULL DEFAULT (1) COMMENT '모자이크 여부'
	, `leaked`				BIT NOT NULL DEFAULT (1) COMMENT '노 모자이크 유출 작품 여부'
	, `reg_date`			DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP() COMMENT '정보 수집시각'

	, PRIMARY KEY (`file_no`) USING BTREE
	, INDEX `IX_FILM_NO` (`film_no`) USING BTREE
	, UNIQUE INDEX `UK_FILE_NAME_FILE_SIZE` (`file_name`, `file_size`) USING BTREE
)
COMMENT='수집한 FILM 파일 정보 테이블'
COLLATE='utf8mb4_unicode_ci'
ENGINE=InnoDB
;
