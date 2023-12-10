-- https://mariadb.com/kb/en/create-function/
-- DROP FUNCTION IF EXISTS fn_has_ai_unpixelated();
DELIMITER //
CREATE OR REPLACE FUNCTION fn_has_ai_unpixelated(p_film_id VARCHAR(250) COLLATE utf8mb4_unicode_ci)
RETURNS INT DETERMINISTIC 
COMMENT 'AI 모자이크 제거 작품을 갖고 있는지에 대한 여부'
BEGIN
	DECLARE v_has_ai_unpixelated INT;

	SET v_has_ai_unpixelated = (
		SELECT
			IFNULL(COUNT(*), 0)
		FROM `FILM` AS F 
			INNER JOIN `COMMENTS` AS C ON (C.film_no = F.film_no)
				AND (C.film_comment LIKE '모파%')
		WHERE 1 = 1
			AND F.film_id = p_film_id
	);

	RETURN v_has_ai_unpixelated;
END//
DELIMITER ;

/*
EXPLAIN
SELECT
	A.film_id, fn_has_ai_unpixelated(A.film_id) AS 'ai_unpixelated'
FROM `AVGOSU` AS A
WHERE 1 = 1
ORDER BY A.avgosu_no DESC
LIMIT 0, 20
;

*/

