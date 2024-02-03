-- 자막 갖고 있는 FHD 영상 목록
SELECT
	A.film_id, A.file_size, A.avgosu_date, A.title
	, CONCAT('https://avgosu6.com/torrent/etc/', A.avgosu_board_no, '.html') AS detail_url
	, CONCAT('magnet:?xt=urn:btih:', HEX(A.magnet_info)) as magnet_addr
	, VA.has_hellven_script AS h
	, VA.has_yamoon_script AS y
FROM `V_AVGOSU_HAS_SCRIPT` AS VA
	INNER JOIN `AVGOSU` AS A ON A.avgosu_no = VA.avgosu_no
WHERE 1 = 1
	AND VA.has_script = 1
	AND resolution = 'F'
ORDER BY VA.avgosu_no DESC
LIMIT 0, 30
;
