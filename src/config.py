# -*- coding: utf-8 -*-
# 영상 정보 관리 시스템 - 설정 관리
# made : hbesthee@naver.com
# date : 2026-06-02

import json
import argparse
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from src.models import ConfigKey, ConfigDef, ResolutionMode



class ConfigManager:
	"""JSON 설정 파일을 읽고 쓰며 설정 값을 제공하는 클래스."""

	def __init__(self, config_file: str = ConfigDef.CONFIG_FILE):
		"""ConfigManager를 초기화하고 설정 파일을 로드하거나 기본 설정을 생성합니다.

		Args:
			config_file (str): 설정 파일 경로 (기본값: conf/encode.json)
		"""
		self.config_file = Path(config_file)
		self.config: Dict[str, Any] = {}
		self.logger = logging.getLogger(__name__)
		self.reload()


	def _get_default_config(self) -> Dict[str, Any]:
		"""ConfigDef에 정의된 기본 설정 값을 반환합니다.

		Returns:
			Dict[str, Any]: 기본 설정 값으로 채워진 딕셔너리
		"""
		return {
			ConfigKey.FFMPEG_PATH: ConfigDef.DEFAULT_FFMPEG
			, ConfigKey.FFPROBE_PATH: ConfigDef.DEFAULT_FFPROBE
			, ConfigKey.INPUT_DIR: ConfigDef.DEFAULT_INPUT_DIR
			, ConfigKey.OUTPUT_DIR: ConfigDef.DEFAULT_OUTPUT_DIR
			, ConfigKey.SUBTITLE_DIR: ConfigDef.DEFAULT_SUBTITLE_DIR
			, ConfigKey.LOG_DIR: ConfigDef.DEFAULT_LOG_DIR
			, ConfigKey.CRF: ConfigDef.DEFAULT_CRF
			, ConfigKey.VOLUME: ConfigDef.DEFAULT_VOLUME
			, ConfigKey.AUDIO_BITRATE: ConfigDef.DEFAULT_AUDIO_BITRATE
			, ConfigKey.DEFAULT_RESOLUTION: ResolutionMode.HD.value
		}


	def _save_config(self) -> None:
		"""현재 설정을 JSON 파일로 저장합니다. 필요 시 상위 디렉토리도 생성합니다."""
		self.config_file.parent.mkdir(parents=True, exist_ok=True)
		with open(self.config_file, 'w', encoding='utf-8') as f:
			json.dump(self.config, f, indent=2, ensure_ascii=False)
		self.logger.info(f"Config saved to {self.config_file}")


	def get(self, key: str, default: Any=None) -> Any:
		"""설정 값을 반환합니다.

		Args:
			key (str): 설정 키
			default (Any, optional): 키가 없을 경우 반환할 기본값

		Returns:
			Any: 설정 값 또는 기본값
		"""
		return self.config.get(key, default)


	def _backup_config_file(self) -> Path:
		"""현재 설정 파일을 '<파일명>.<YYYYmmdd-HHMMSS>.bak' 으로 복사하여 보관합니다.
		같은 이름의 백업이 있으면 일련번호를 붙여 기존 백업을 덮어쓰지 않습니다.

		Returns:
			Path: 백업 파일 경로
		"""
		timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
		backup_file = self.config_file.with_name(f"{self.config_file.name}.{timestamp}.bak")
		sequence = 1
		while (backup_file.exists()):
			backup_file = self.config_file.with_name(f"{self.config_file.name}.{timestamp}-{sequence}.bak")
			sequence += 1
		shutil.copy2(self.config_file, backup_file)
		return backup_file


	def reload(self) -> None:
		"""설정 파일이 존재하면 로드하고, 없으면 기본 설정으로 새 파일을 생성합니다.
		파일 내용이 JSON 객체(dict)가 아니면 원본을 백업한 뒤 기본 설정으로 대체합니다.
		"""
		if (not self.config_file.exists()):
			self.config = self._get_default_config()
			self._save_config()
			self.logger.info(f"Default settings file created: {self.config_file}")
			return

		self.logger.info(f"Settings loaded: {self.config_file}")
		loaded_config = None
		try:
			with open(self.config_file, 'r', encoding='utf-8') as f:
				loaded_config = json.load(f)
		except json.JSONDecodeError as e:
			self.logger.warning(f"Invalid settings JSON ({e}): {self.config_file}")

		if (isinstance(loaded_config, dict)):
			self.config = loaded_config
			return

		backup_file = self._backup_config_file()
		self.logger.warning(f"Invalid settings format, backup to {backup_file}, use defaults: {self.config_file}")
		self.config = self._get_default_config()
		self._save_config()


	def update_from_args(self, args: argparse.Namespace) -> None:
		"""명령줄 인자 값으로 설정을 업데이트합니다. None 이 아닌 인자만 반영됩니다.

		Args:
			args (argparse.Namespace): argparse 로 파싱된 명령줄 인자
		"""
		if hasattr(args, 'ffmpeg') and args.ffmpeg is not None:
			self.config[ConfigKey.FFMPEG_PATH] = args.ffmpeg
			self.logger.debug(f"FFmpeg path updated: {args.ffmpeg}")
		if hasattr(args, 'ffprobe') and args.ffprobe is not None:
			self.config[ConfigKey.FFPROBE_PATH] = args.ffprobe
			self.logger.debug(f"FFProbe path updated: {args.ffprobe}")
		if hasattr(args, 'input') and args.input is not None:
			self.config[ConfigKey.INPUT_DIR] = args.input
			self.logger.debug(f"Input directory updated: {args.input}")
		if hasattr(args, 'output') and args.output is not None:
			self.config[ConfigKey.OUTPUT_DIR] = args.output
			self.logger.debug(f"Output directory updated: {args.output}")
		if hasattr(args, 'sub') and args.sub is not None:
			self.config[ConfigKey.SUBTITLE_DIR] = args.sub
			self.logger.debug(f"Subtitle directory updated: {args.sub}")
		if hasattr(args, 'crf') and args.crf is not None:
			try:
				self.config[ConfigKey.CRF] = int(args.crf)
				self.logger.debug(f"CRF updated: {args.crf}")
			except:
				pass
		if hasattr(args, 'volume') and args.volume is not None:
			try:
				self.config[ConfigKey.VOLUME] = float(args.volume)
				self.logger.debug(f"Volume updated: {args.volume}")
			except:
				pass
