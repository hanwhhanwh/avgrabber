DELIMITER $$

CREATE OR REPLACE PROCEDURE sp_save_comment
(
	IN p_member_no INT -- 댓글을 입력하는 회원 고유번호
	, IN p_film_id VARCHAR(255) -- 작품 고유 ID
	, IN p_is_owned TINYINT -- 작품 소유 여부 (0 = 미소유, 1 = 소유)
	, IN p_film_rate INT -- 작품에 대한 주관적 점수 (0 ~ 100)
	, IN p_film_comment MEDIUMTEXT -- 작품에 대한 감상/댓글
)
	LANGUAGE SQL
	NOT DETERMINISTIC
	CONTAINS SQL
	SQL SECURITY DEFINER
	COMMENT '작품에 대한 감상/댓글을 저장합니다.
작품정보가 없을 경우에는, 먼저 빈 작품정보를 생성합니다.'
BEGIN


DECLARE v_film_no INT;


-- 작품 고유번호 확인
SELECT
	film_no INTO v_film_no
FROM `FILM`
WHERE 1= 1
	AND film_id = UPPER(p_film_id);

IF v_film_no IS NULL THEN

	-- 신규 작품 추가하기
	INSERT INTO `FILM`
	(member_no, film_id, is_owned)
	VALUES
	(p_member_no, UPPER(p_film_id), p_is_owned);
	
	SET v_film_no = LAST_INSERT_ID();

END IF;

-- 댓글 추가
INSERT INTO `COMMENTS`
(film_no, member_no, film_rate, film_comment)
VALUES
(v_film_no, p_member_no, p_film_rate, p_film_comment);


END$$

DELIMITER ;

