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
from typing import Any, Dict, Optional

from src.models import ConfigKey, ConfigDef, ResolutionMode



class ConfigManager:
	"""JSON 설정 파일을 읽고 쓰며 설정 값을 제공하는 클래스."""

	def __init__(self, config_file: str = ConfigDef.CONFIG_FILE, strict: bool = False):
		"""ConfigManager를 초기화하고 설정 파일을 로드하거나 기본 설정을 생성합니다.

		Args:
			config_file (str): 설정 파일 경로 (기본값: conf/encode.json)
			strict (bool): True 이면 설정 백업 실패 시 예외를 전파합니다. False 이면 경고 후
				기본 설정으로 동작하되 원본 설정 파일은 덮어쓰지 않습니다 (기본값: False)
		"""
		self.config_file = Path(config_file)
		self.strict = strict
		self.backup_failed = False
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
		"""현재 설정을 JSON 파일로 저장합니다. 필요 시 상위 디렉토리도 생성합니다.
		원본 설정 백업에 실패한 상태라면 원본 보존을 위해 저장을 건너뜁니다.
		"""
		if (self.backup_failed):
			self.logger.warning(f"Skip saving settings, original backup failed: {self.config_file}")
			return

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
		"""현재 설정 파일을 '<파일명>.<YYYYmmdd-HHMMSS>[-N].bak' 으로 복사하여 보관합니다.
		같은 시각의 백업이 있으면 일련번호를 키워 기존 백업을 덮어쓰지 않습니다.
		보관 개수는 ConfigDef.MAX_CONFIG_BACKUPS 를 넘지 않도록 오래된 백업을 정리합니다.

		Returns:
			Path: 백업 파일 경로
		"""
		timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
		existing_backups = sorted(
			self.config_file.parent.glob(f"{self.config_file.name}.{timestamp}*.bak")
			, key=self._backup_order_key
		)
		sequence = (self._backup_order_key(existing_backups[-1])[1] + 1) if (existing_backups) else 0
		suffix = f"-{sequence}" if (0 < sequence) else ""
		backup_file = self.config_file.parent / f"{self.config_file.name}.{timestamp}{suffix}.bak"

		shutil.copy2(self.config_file, backup_file)
		self._prune_backups(protect=backup_file)

		return backup_file


	def _backup_order_key(self, backup_file: Path) -> tuple:
		"""백업 파일명에서 (타임스탬프, 일련번호) 정렬 키를 만듭니다.

		Args:
			backup_file (Path): 백업 파일 경로

		Returns:
			tuple: (타임스탬프 문자열, 일련번호 정수) 튜플
		"""
		stem = backup_file.name[len(self.config_file.name) + 1:-len(".bak")]
		timestamp = stem[:15]
		sequence = stem[15:]

		return (timestamp, int(sequence[1:]) if (sequence) else 0)


	def _prune_backups(self, protect: Optional[Path] = None) -> None:
		"""최근 ConfigDef.MAX_CONFIG_BACKUPS 개만 남기고 오래된 설정 백업을 삭제합니다.

		Args:
			protect (Optional[Path]): 삭제 대상에서 제외할 백업 파일 (방금 생성한 백업)
		"""
		backup_files = sorted(
			self.config_file.parent.glob(f"{self.config_file.name}.*.bak")
			, key=self._backup_order_key
		)
		for backup_file in backup_files[:-ConfigDef.MAX_CONFIG_BACKUPS]:
			if ((protect is not None) and (backup_file == protect)):
				continue
			try:
				backup_file.unlink(missing_ok=True)
			except OSError as e:
				self.logger.warning(f"Failed to remove old settings backup {backup_file}: {e}")


	def reload(self) -> None:
		"""설정 파일이 존재하면 로드하고, 없으면 기본 설정으로 새 파일을 생성합니다.
		파일 내용이 JSON 객체(dict)가 아니면 원본을 백업한 뒤 기본 설정으로 대체합니다.
		"""
		self.backup_failed = False
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

		try:
			backup_file = self._backup_config_file()
		except OSError as e:
			if (self.strict):
				raise
			self.backup_failed = True
			self.logger.error(f"Settings backup failed ({e}), use defaults without saving: {self.config_file}")
			self.config = self._get_default_config()
			return

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
