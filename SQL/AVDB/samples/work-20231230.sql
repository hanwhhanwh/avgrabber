SELECT
	A.film_id, A.file_size, A.resolution, A.title, CONCAT('https://avgosu5.com', A.detail_url)
	, A.magnet_addr, Y.script_name, A.avgosu_date, C.film_no, F.film_id, C.film_comment
FROM `AVGOSU` AS A
	INNER JOIN `SCRIPTS_YAMOON` AS Y
		ON Y.film_id = A.film_id
	LEFT OUTER JOIN `FILM` AS F
		ON F.film_id = A.film_id
	LEFT OUTER JOIN `COMMENTS` AS C
		ON F.film_no = C.film_no -- AND (C.film_comment LIKE '모파.%')
		-- AND C.film_no IS NULL
WHERE 1 = 1
	AND A.film_id LIKE 'MIDE-7%'
	-- AND NOT EXISTS (SELECT * FROM COMMENTS AS CM INNER JOIN FILM AS F ON F.film_no = CM.film_no WHERE F.film_id = A.film_id)
ORDER BY A.avgosu_no DESC
LIMIT 0, 30;

-- 2023-10-14 ; 698개의 작품이 매핑됨
/*
SELECT
	film_id, COUNT(film_id) AS film_count
FROM `AVGOSU`
WHERE 1 = 1
GROUP BY film_id
HAVING film_count > 1

SELECT * FROM `AVGOSU` AS A WHERE A.film_id = 'JUL-960'
;
SELECT * FROM `SCRIPTS_YAMOON` AS Y WHERE Y.film_id = 'JUL-960'


SELECT * FROM `AVGOSU` AS A 
	INNER JOIN `SCRIPTS_YAMOON` AS Y
		ON Y.film_id = A.film_id
WHERE A.film_id = 'JUL-960'
;

SELECT
	*
FROM `AVGOSU` AS A
WHERE file_size LIKE '2.%'

UPDATE `AVGOSU` SET
	resolution = 'H'
WHERE file_size LIKE '2.%'


UPDATE `AVGOSU` SET
	detail_url = REPLACE(detail_url, 'https://avgosu1.com', '')
	, cover_image_url = REPLACE(cover_image_url, 'https://avgosu1.com', '')
	, thumbnail_url = REPLACE(thumbnail_url, 'https://avgosu1.com', '')

SELECT * FROM AVGOSU WHERE film_id LIKE 'FSDSS-%'
;


SELECT
	A.film_id, A.file_size, A.avgosu_date, A.title
	, CONCAT('https://avgosu5.com', A.detail_url) AS detail_url
	, A.magnet_addr
	, fn_has_yamoon_script(A.film_id) AS has_scirpt
FROM `AVGOSU` AS A
WHERE 1 = 1
	-- AND A.film_id LIKE 'JUL-960'
	-- AND NOT EXISTS (SELECT * FROM COMMENTS AS CM INNER JOIN FILM AS F ON F.film_no = CM.film_no WHERE F.film_id = A.film_id)
	AND ( (fn_has_yamoon_script(A.film_id) > 0) OR (fn_has_hellven_script(A.film_id) > 0) )
	AND resolution = 'F'
ORDER BY A.avgosu_no DESC
LIMIT 0, 30;
*/