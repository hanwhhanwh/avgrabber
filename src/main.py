# -*- coding: utf-8 -*-
# 영상 정보 관리 시스템 (FFmpeg 동영상 인코딩 / 웹 인터페이스)
# made : hbesthee@naver.com
# date : 2025-12-14
# note : 진입점 — core 로직은 모듈(encoder, config, web_service 등)로 분산됨

import logging
import sys
from pathlib import Path

import uvicorn

# 프로젝트 루트를 sys.path 에 추가 (src/ 내부에서 실행 시 필요)
_project_root = str(Path(__file__).resolve().parent.parent)
if (_project_root not in sys.path):
	sys.path.insert(0, _project_root)

from src.config import ConfigManager
from src.models import ConfigKey
from src.encoder import VideoEncoder
from src.web_service import create_app

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)



def main():
	logger.info("FFmpeg 웹 기반 동영상 인코딩 시스템 시작")

	try:
		encoder = VideoEncoder()
		args = encoder.parse_arguments()

		print("\n" + "="*70)
		print("FFmpeg 웹 기반 동영상 인코딩 시스템")
		print("="*70)
		encoder.print_config()
		print("="*70)
		print(f"\n웹 인터페이스: http://localhost:{args.port}")
		print("="*70 + "\n")

		app = create_app(encoder)
		
		logger.info(f"uvicorn 를 http://0.0.0.0:{args.port} 로 시작")
		uvicorn.run(app, host="0.0.0.0", port=args.port)
	except Exception as e:
		logger.error(f"초기화 오류: {e}")
		raise



if (__name__ == "__main__"):
	main()
