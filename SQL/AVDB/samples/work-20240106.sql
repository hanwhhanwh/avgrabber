-- magnet:?xt=urn:btih:ec5323417ee66652f8b9fbd3cb693374231cefcc
SELECT
	magnet_addr, SUBSTRING(magnet_addr, 21) AS mag_net_info_str
	, UNHEX(SUBSTRING(magnet_addr, 21)) AS mag_net_info
FROM AVGOSU AS A
WHERE 1 = 1
LIMIT 10;

SELECT
	detail_url, REGEXP_SUBSTR(detail_url, '(\\d+)') AS board_no
FROM AVGOSU AS A
WHERE 1 = 1
LIMIT 10;


UPDATE `AVGOSU` SET
	`avgosu_board_no` = REGEXP_SUBSTR(detail_url, '(\\d+)')
	, `magnet_info` = UNHEX(SUBSTRING(magnet_addr, 21))
;
/* 영향 받은 행: 5,311  찾은 행: 0  경고: 0  지속 시간 1 쿼리: 2.094 초 */


UPDATE `AVGOSU` SET
	`cover_image_url` = REPLACE(`cover_image_url`, '/uploads/images', '')
	, `thumbnail_url` = REPLACE(`thumbnail_url`, '/uploads/images', '')
;
/* 영향 받은 행: 5,311  찾은 행: 0  경고: 0  지속 시간 1 쿼리: 1.156 초 */