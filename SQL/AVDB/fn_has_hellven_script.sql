-- https://mariadb.com/kb/en/create-function/
-- DROP FUNCTION IF EXISTS fn_has_hellven_script();
DELIMITER //
CREATE OR REPLACE FUNCTION fn_has_hellven_script(p_film_id VARCHAR(250) COLLATE utf8mb4_unicode_ci)
RETURNS INT DETERMINISTIC 
COMMENT 'HELLVEN 자막을 갖고 있는지에 대한 여부'
BEGIN
	DECLARE v_has_hellven_script INT;

	SET v_has_hellven_script = (
		SELECT
			IFNULL(COUNT(*), 0)
		FROM SCRIPTS_HELLVEN AS Y
		WHERE 1 = 1
			AND Y.film_id = p_film_id
	);

	RETURN v_has_hellven_script;
END//
DELIMITER ;

/*
EXPLAIN SELECT
	A.film_id, fn_has_hellven_script(A.film_id) AS 'has_hellven'
FROM `AVGOSU` AS A
WHERE 1 = 1
ORDER BY A.avgosu_no DESC
LIMIT 0, 20
;

*/

