-- https://mariadb.com/kb/en/create-function/
-- DROP FUNCTION IF EXISTS fn_has_comment();
DELIMITER //
CREATE OR REPLACE FUNCTION fn_has_comment(p_film_id VARCHAR(250) COLLATE utf8mb4_unicode_ci)
RETURNS INT DETERMINISTIC 
COMMENT '댓글 평을 갖고 있는지에 대한 여부'
BEGIN
	DECLARE v_has_comment INT;

	SET v_has_comment = (
		SELECT
			IFNULL(COUNT(*), 0)
		FROM `FILM` AS F 
			INNER JOIN `COMMENTS` AS C ON C.film_no = F.film_no
		WHERE 1 = 1
			AND F.film_id = p_film_id
	);

	RETURN v_has_comment;
END//
DELIMITER ;

/*
EXPLAIN
SELECT
	A.film_id, fn_has_comment(A.film_id) AS 'has_comment'
FROM `AVGOSU` AS A
WHERE 1 = 1
ORDER BY A.avgosu_no DESC
LIMIT 195, 20
;

*/

