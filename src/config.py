# -*- coding: utf-8 -*-
# 영상 정보 관리 시스템 - 설정 관리
# made : hbesthee@naver.com
# date : 2026-06-02

import json
import re
import argparse
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Final, List, Optional, Tuple

from src.models import ConfigKey, ConfigDef, ResolutionMode, VideoCodec


CONFIG_BACKUP_PATTERN: Final[re.Pattern] = re.compile(r"\.(\d{8}-\d{6})(?:-(\d+))?\.bak$")



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
			, ConfigKey.VIDEO_CODEC: ConfigDef.DEFAULT_VIDEO_CODEC
			, ConfigKey.SVTAV1_PRESET: ConfigDef.DEFAULT_SVTAV1_PRESET
			, ConfigKey.SVTAV1_BIT_DEPTH: ConfigDef.DEFAULT_SVTAV1_BIT_DEPTH
			, ConfigKey.X265_PRESET: ConfigDef.DEFAULT_X265_PRESET
			, ConfigKey.CRF: ConfigDef.DEFAULT_CRF
			, ConfigKey.VOLUME: ConfigDef.DEFAULT_VOLUME
			, ConfigKey.AUDIO_BITRATE: ConfigDef.DEFAULT_AUDIO_BITRATE
			, ConfigKey.SEARCH_SUBFOLDERS: ConfigDef.DEFAULT_SEARCH_SUBFOLDERS
			, ConfigKey.PRESERVE_FOLDER_STRUCTURE: ConfigDef.DEFAULT_PRESERVE_FOLDER_STRUCTURE
			, ConfigKey.DEFAULT_RESOLUTION: ResolutionMode.HD.value
		}


	def _save_config(self) -> bool:
		"""현재 설정을 JSON 파일로 저장합니다. 필요 시 상위 디렉토리도 생성합니다.
		원본 설정 백업에 실패한 상태라면 원본 보존을 위해 저장을 건너뜁니다.

		Returns:
			bool: 파일에 저장했으면 True, 백업 실패로 건너뛰었으면 False
		"""
		if (self.backup_failed):
			self.logger.warning(f"Skip saving settings, original backup failed: {self.config_file}")
			return False

		self.config_file.parent.mkdir(parents=True, exist_ok=True)
		with open(self.config_file, 'w', encoding='utf-8') as f:
			json.dump(self.config, f, indent=2, ensure_ascii=False)
		self.logger.info(f"Config saved to {self.config_file}")

		return True


	def get(self, key: str, default: Any=None) -> Any:
		"""설정 값을 반환합니다.

		Args:
			key (str): 설정 키
			default (Any, optional): 키가 없을 경우 반환할 기본값

		Returns:
			Any: 설정 값 또는 기본값
		"""
		return self.config.get(key, default)


	def get_all(self) -> Dict[str, Any]:
		"""기본값을 포함한 전체 설정 값을 반환합니다.

		Returns:
			Dict[str, Any]: 기본 설정에 현재 설정 값을 덮어쓴 딕셔너리
		"""
		return {**self._get_default_config(), **self.config}


	def update_values(self, values: Dict[str, Any]) -> bool:
		"""설정 값을 메모리에 반영하고 설정 파일에 저장합니다.

		Args:
			values (Dict[str, Any]): 반영할 설정 키와 값

		Returns:
			bool: 파일에 저장했으면 True, 백업 실패로 건너뛰었으면 False
		"""
		self.config.update(values)
		return self._save_config()


	def validate_updates(self, values: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, str]]:
		"""웹 설정 페이지에서 받은 값을 검증하고 정규화합니다.

		Args:
			values (Dict[str, Any]): 검증할 설정 키와 값

		Returns:
			Tuple[Dict[str, Any], Dict[str, str]]: 정규화된 설정 값과 키별 오류 메시지
		"""
		text_keys = {
			ConfigKey.FFMPEG_PATH: "FFmpeg 경로",
			ConfigKey.FFPROBE_PATH: "FFprobe 경로",
			ConfigKey.INPUT_DIR: "입력 디렉토리",
			ConfigKey.OUTPUT_DIR: "출력 디렉토리",
			ConfigKey.SUBTITLE_DIR: "자막 디렉토리",
			ConfigKey.LOG_DIR: "로그 디렉토리",
			ConfigKey.AUDIO_BITRATE: "오디오 비트레이트"
		}
		applied: Dict[str, Any] = {}
		errors: Dict[str, str] = {}

		for key, value in values.items():
			try:
				if (key in text_keys):
					applied[key] = self._validate_text(value, text_keys[key])
				elif (key == ConfigKey.CRF):
					applied[key] = None if (value in (None, "")) else self._validate_int(value, "CRF", 0, 63)
				elif (key == ConfigKey.SVTAV1_PRESET):
					applied[key] = self._validate_int(value, "SVT-AV1 preset", 0, 13)
				elif (key == ConfigKey.X265_PRESET):
					applied[key] = self._validate_choice(value, "x265 preset", ConfigDef.X265_PRESETS)
				elif (key == ConfigKey.SVTAV1_BIT_DEPTH):
					bit_depth = self._validate_int(value, "비트 깊이", 8, 10)
					if (bit_depth not in (8, 10)):
						raise ValueError("비트 깊이는 8 또는 10이어야 합니다")
					applied[key] = bit_depth
				elif (key == ConfigKey.SEARCH_SUBFOLDERS):
					applied[key] = self._validate_bool(value, "하위 폴더 검색")
				elif (key == ConfigKey.PRESERVE_FOLDER_STRUCTURE):
					applied[key] = self._validate_bool(value, "원본 폴더 구조 유지")
				elif (key == ConfigKey.VOLUME):
					applied[key] = self._validate_float(value, "볼륨", 0.0, 10.0)
				elif (key == ConfigKey.VIDEO_CODEC):
					applied[key] = self._validate_choice(value, "영상 코덱", tuple(codec.value for codec in VideoCodec))
				elif (key == ConfigKey.DEFAULT_RESOLUTION):
					applied[key] = self._validate_choice(value, "기본 해상도", tuple(mode.value for mode in ResolutionMode))
				else:
					errors[key] = "알 수 없는 설정 항목입니다"
			except ValueError as e:
				errors[key] = str(e)

		return applied, errors


	@staticmethod
	def _validate_text(value: Any, label: str) -> str:
		"""비어 있지 않은 문자열 설정 값을 검증합니다.

		Args:
			value (Any): 검증할 값
			label (str): 오류 메시지에 표시할 항목 이름

		Returns:
			str: 앞뒤 공백을 제거한 문자열

		Raises:
			ValueError: 문자열이 아니거나 비어 있을 때
		"""
		if ((not isinstance(value, str)) or (not value.strip())):
			raise ValueError(f"{label} 값을 입력해야 합니다")
		return value.strip()


	@staticmethod
	def _validate_int(value: Any, label: str, minimum: int, maximum: int) -> int:
		"""정수 설정 값을 범위와 함께 검증합니다.

		Args:
			value (Any): 검증할 값
			label (str): 오류 메시지에 표시할 항목 이름
			minimum (int): 허용하는 최소값
			maximum (int): 허용하는 최대값

		Returns:
			int: 검증된 정수 값

		Raises:
			ValueError: 정수가 아니거나 범위를 벗어날 때
		"""
		if ((isinstance(value, bool)) or (isinstance(value, float) and (not value.is_integer()))):
			raise ValueError(f"{label} 값은 정수여야 합니다")
		try:
			number = int(value)
		except (TypeError, ValueError):
			raise ValueError(f"{label} 값은 정수여야 합니다")
		if (not (minimum <= number <= maximum)):
			raise ValueError(f"{label} 값은 {minimum}~{maximum} 범위여야 합니다")
		return number


	@staticmethod
	def _validate_float(value: Any, label: str, minimum: float, maximum: float) -> float:
		"""실수 설정 값을 범위와 함께 검증합니다.

		Args:
			value (Any): 검증할 값
			label (str): 오류 메시지에 표시할 항목 이름
			minimum (float): 허용하는 최소값
			maximum (float): 허용하는 최대값

		Returns:
			float: 검증된 실수 값

		Raises:
			ValueError: 실수가 아니거나 범위를 벗어날 때
		"""
		if (isinstance(value, bool)):
			raise ValueError(f"{label} 값은 숫자여야 합니다")
		try:
			number = float(value)
		except (TypeError, ValueError):
			raise ValueError(f"{label} 값은 숫자여야 합니다")
		if (not (minimum <= number <= maximum)):
			raise ValueError(f"{label} 값은 {minimum}~{maximum} 범위여야 합니다")
		return number


	@staticmethod
	def _validate_choice(value: Any, label: str, choices: Tuple[str, ...]) -> str:
		"""정해진 선택지 중 하나인지 검증하고 정규화된 값을 반환합니다.

		Args:
			value (Any): 검증할 값
			label (str): 오류 메시지에 표시할 항목 이름
			choices (Tuple[str, ...]): 허용하는 값 목록

		Returns:
			str: 선택지에 정의된 정규화된 값

		Raises:
			ValueError: 문자열이 아니거나 선택지에 없을 때
		"""
		if (not isinstance(value, str)):
			raise ValueError(f"{label} 값이 올바르지 않습니다")
		normalized = value.strip().lower()
		for choice in choices:
			if (normalized == choice.lower()):
				return choice
		raise ValueError(f"{label} 값은 {', '.join(choices)} 중 하나여야 합니다")


	@staticmethod
	def _validate_bool(value: Any, label: str) -> bool:
		"""참/거짓 설정 값을 검증합니다.

		Args:
			value (Any): 검증할 값
			label (str): 오류 메시지에 표시할 항목 이름

		Returns:
			bool: 검증된 참/거짓 값

		Raises:
			ValueError: 참/거짓으로 해석할 수 없을 때
		"""
		if (isinstance(value, bool)):
			return value
		if (isinstance(value, str)):
			normalized = value.strip().lower()
			if (normalized in ("1", "true", "yes", "on")):
				return True
			if (normalized in ("0", "false", "no", "off")):
				return False
		raise ValueError(f"{label} 값은 true 또는 false 여야 합니다")


	def _backup_config_file(self) -> Path:
		"""현재 설정 파일을 '<파일명>.<YYYYmmdd-HHMMSS>[-N].bak' 으로 복사하여 보관합니다.
		같은 시각의 백업이 있으면 일련번호를 키워 기존 백업을 덮어쓰지 않습니다.
		보관 개수는 ConfigDef.MAX_CONFIG_BACKUPS 를 넘지 않도록 오래된 백업을 정리합니다.

		Returns:
			Path: 백업 파일 경로
		"""
		timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
		existing_backups = self._find_backup_files(f"{self.config_file.name}.{timestamp}*.bak")
		sequence = (self._backup_order_key(existing_backups[-1])[1] + 1) if (existing_backups) else 0
		suffix = f"-{sequence}" if (0 < sequence) else ""
		backup_file = self.config_file.parent / f"{self.config_file.name}.{timestamp}{suffix}.bak"

		shutil.copy2(self.config_file, backup_file)
		self._prune_backups(protect=backup_file)

		return backup_file


	def _find_backup_files(self, pattern: str) -> List[Path]:
		"""glob 패턴에 맞는 파일 중 백업명 규칙을 만족하는 것만 오래된 순으로 반환합니다.

		Args:
			pattern (str): 검색할 glob 패턴

		Returns:
			List[Path]: 백업명 규칙을 만족하는 백업 파일 목록 (오래된 것부터)
		"""
		backup_files = []
		for backup_file in self.config_file.parent.glob(pattern):
			order_key = self._backup_order_key(backup_file)
			if (order_key is not None):
				backup_files.append((order_key, backup_file))
		backup_files.sort(key=lambda item: item[0])

		return [backup_file for _, backup_file in backup_files]


	def _backup_order_key(self, backup_file: Path) -> Optional[tuple]:
		"""백업 파일명에서 (타임스탬프, 일련번호) 정렬 키를 만듭니다.

		Args:
			backup_file (Path): 백업 파일 경로

		Returns:
			Optional[tuple]: 백업명 규칙을 만족하면 (타임스탬프, 일련번호), 아니면 None
		"""
		matched = CONFIG_BACKUP_PATTERN.search(backup_file.name)
		if (matched is None):
			return None

		timestamp = matched.group(1)
		sequence = matched.group(2)

		return (timestamp, int(sequence) if (sequence) else 0)


	def _prune_backups(self, protect: Optional[Path] = None) -> None:
		"""최근 ConfigDef.MAX_CONFIG_BACKUPS 개만 남기고 오래된 설정 백업을 삭제합니다.
		백업명 규칙을 벗어난 파일은 정리 대상에서 제외합니다.

		Args:
			protect (Optional[Path]): 삭제 대상에서 제외할 백업 파일 (방금 생성한 백업)
		"""
		backup_files = self._find_backup_files(f"{self.config_file.name}.*.bak")
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
