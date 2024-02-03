-- 자막 소유 여부 확인을 위한 뷰
-- DROP VIEW V_AVGOSU_HAS_SCRIPT;
CREATE OR REPLACE VIEW V_AVGOSU_HAS_SCRIPT AS
	SELECT
		A.avgosu_no
		, IF(H.script_hellven_no IS NULL, IF(Y.script_yamoon_no IS NULL, 0, 1), 1) AS has_script
		, H.script_hellven_no
		, IF(H.script_hellven_no IS NULL, 0, 1) AS has_hellven_script
		, Y.script_yamoon_no
		, IF(Y.script_yamoon_no IS NULL, 0, 1) AS has_yamoon_script
	FROM `AVGOSU` AS A
		LEFT OUTER JOIN `SCRIPTS_HELLVEN` AS H ON H.film_id = A.film_id
		LEFT OUTER JOIN `SCRIPTS_YAMOON` AS Y ON Y.film_id = A.film_id
;
/*
EXPLAIN
SELECT
	AHS.*
FROM V_AVGOSU_HAS_SCRIPT AS AHS
ORDER BY 1 DESC
LIMIT 100
;

*/