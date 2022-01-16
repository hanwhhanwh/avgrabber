-- DROP TABLE IF EXISTS `PRODUCT_COMPANY`
CREATE TABLE IF NOT EXISTS `PRODUCT_COMPANY`
(
	`product_company_no`	INT NOT NULL AUTO_INCREMENT COMMENT '제작사 고유번호'
	, `member_no`			INT NOT NULL COMMENT '작성자 고유번호 (FK: MEMBER.member_no)'
	, `product_company_name`	VARCHAR(100) NOT NULL COMMENT '제작사 이름' COLLATE 'utf8_general_ci'
	, `reg_date`			DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP() COMMENT '정보 등록시각'

	, PRIMARY KEY (`product_company_no`) USING BTREE
)
COMMENT='제작사 정보 관리 테이블'
COLLATE='utf8_general_ci'
ENGINE=InnoDB
;
