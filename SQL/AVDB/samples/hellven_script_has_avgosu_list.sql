-- hellen 자막 중 avgosu에 있는 FHD 영상 목록
-- EXPLAIN
SELECT
	A.film_id, A.file_size, H.board_date, A.title
	, CONCAT('https://avgosu6.com/torrent/etc/', A.avgosu_board_no, '.html') AS detail_url
	, CONCAT('magnet:?xt=urn:btih:', HEX(A.magnet_info)) as magnet_addr
FROM `SCRIPTS_HELLVEN` AS H 
	INNER JOIN `AVGOSU` AS A ON A.film_id = H.film_id
		AND resolution = 'F'
WHERE 1 = 1
ORDER BY H.script_hellven_no DESC
LIMIT 330, 30
;

/*
-- EXPLAIN
SELECT
	A.film_id, A.file_size, H.board_date, A.title
	, CONCAT('https://avgosu6.com/torrent/etc/', A.avgosu_board_no, '.html') AS detail_url
	, CONCAT('magnet:?xt=urn:btih:', HEX(A.magnet_info)) as magnet_addr
	, VA.has_hellven_script AS h
	, VA.has_yamoon_script AS y
FROM `V_AVGOSU_HAS_SCRIPT` AS VA
	INNER JOIN `AVGOSU` AS A ON A.avgosu_no = VA.avgosu_no
	INNER JOIN `SCRIPTS_HELLVEN` AS H ON H.script_hellven_no = VA.script_hellven_no
WHERE 1 = 1
	AND VA.has_script = 1
	AND resolution = 'F'
ORDER BY VA.script_hellven_no DESC
LIMIT 0, 30
;
*/