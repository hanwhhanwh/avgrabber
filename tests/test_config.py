# -*- coding: utf-8 -*-
# ConfigManager tests - 30+ test cases covering various scenarios.
# made : hbesthee@naver.com
# date : 2026-06-02

from pathlib import Path

import json
import logging
import os
import sys
import tempfile
import argparse
from datetime import datetime, timedelta


import pytest


# 프로젝트 루트를 sys.path 에 추가 (src/ 내부에서 실행 시 필요)
_project_root = str(Path(__file__).resolve().parent.parent)
if (_project_root not in sys.path):
    sys.path.insert(0, _project_root)

from src.config import ConfigManager
from src.models import ConfigKey, ConfigDef, ResolutionMode


class MockArgs:
	"""Mock argparse.Namespace object."""
	def __init__(self, **kwargs):
		self.kwargs = kwargs
	
	def __getattr__(self, name):
		return self.kwargs.get(name, None)


@pytest.fixture
def temp_dir():
	"""Create a temporary directory for config tests."""
	tmp = tempfile.mkdtemp()
	yield tmp
	import shutil
	shutil.rmtree(tmp)


@pytest.fixture
def config_file(temp_dir):
	"""Create a temporary config file."""
	config_path = os.path.join(temp_dir, "test_config.json")
	yield config_path


@pytest.fixture
def config_manager(config_file):
	"""Create ConfigManager instance with test config file."""
	return ConfigManager(config_file)


# ==================== ====================
# Test Suite: Initialization
# ==================== ====================

class TestConfigManagerInitialization:
	"""Test ConfigManager initialization."""
	
	def test_init_with_valid_config_file(self, config_file, config_manager: ConfigManager):
		"""Test initialization with valid config file exists."""
		assert config_manager.config_file == Path(config_file)
		assert isinstance(config_manager.config, dict)
	
	def test_init_creates_default_config(self, config_file, config_manager: ConfigManager):
		"""Test initialization creates default config when file doesn't exist."""
		# Verify config has required keys
		required_keys = [
			ConfigKey.FFMPEG_PATH, ConfigKey.FFPROBE_PATH, ConfigKey.INPUT_DIR,
			ConfigKey.OUTPUT_DIR, ConfigKey.SUBTITLE_DIR, ConfigKey.LOG_DIR,
			ConfigKey.CRF, ConfigKey.VOLUME, ConfigKey.AUDIO_BITRATE,
			ConfigKey.DEFAULT_RESOLUTION
		]
		for key in required_keys:
			assert key in config_manager.config
	
	def test_init_with_nonexistent_file(self, temp_dir, config_manager: ConfigManager):
		"""Test initialization with completely nonexistent file path."""
		nonexistent = os.path.join(temp_dir, "nonexistent.json")
		assert config_manager.config_file != Path(nonexistent)
		assert config_manager.config[ConfigKey.CRF] == ConfigDef.DEFAULT_CRF


# ==================== ====================
# Test Suite: Default Configuration
# ==================== ====================

class TestDefaultConfiguration:
	"""Test default configuration values."""
	
	def test_default_ffmpeg_path(self, config_manager: ConfigManager):
		"""Test default FFmpeg path matches ConfigDef.DEFAULT_FFMPEG."""
		assert ConfigManager(config_manager.config_file)._get_default_config()[
			ConfigKey.FFMPEG_PATH] == ConfigDef.DEFAULT_FFMPEG
	
	def test_default_ffprobe_path(self, config_manager: ConfigManager):
		"""Test default FFprobe path matches ConfigDef.DEFAULT_FFPROBE."""
		assert ConfigManager(config_manager.config_file)._get_default_config()[
			ConfigKey.FFPROBE_PATH] == ConfigDef.DEFAULT_FFPROBE
	
	def test_default_crf(self, config_manager: ConfigManager):
		"""Test default CRF value."""
		default_config = ConfigManager(config_manager.config_file)._get_default_config()
		assert default_config[ConfigKey.CRF] == ConfigDef.DEFAULT_CRF
	
	def test_default_volume(self, config_manager: ConfigManager):
		"""Test default volume value."""
		default_config = ConfigManager(config_manager.config_file)._get_default_config()
		assert default_config[ConfigKey.VOLUME] == ConfigDef.DEFAULT_VOLUME
	
	def test_default_audio_bitrate(self, config_manager: ConfigManager):
		"""Test default audio bitrate value."""
		default_config = ConfigManager(config_manager.config_file)._get_default_config()
		assert default_config[ConfigKey.AUDIO_BITRATE] == ConfigDef.DEFAULT_AUDIO_BITRATE

	def test_default_resolution(self, config_manager: ConfigManager):
		"""Test default resolution is HD."""
		default_config = ConfigManager(config_manager.config_file)._get_default_config()
		assert default_config[ConfigKey.DEFAULT_RESOLUTION] == ResolutionMode.HD.value
	
	def test_default_input_dir(self, config_manager: ConfigManager):
		"""Test default input directory."""
		default_config = ConfigManager(config_manager.config_file)._get_default_config()
		assert default_config[ConfigKey.INPUT_DIR] == ConfigDef.DEFAULT_INPUT_DIR
	
	def test_default_output_dir(self, config_manager: ConfigManager):
		"""Test default output directory."""
		default_config = ConfigManager(config_manager.config_file)._get_default_config()
		assert default_config[ConfigKey.OUTPUT_DIR] == ConfigDef.DEFAULT_OUTPUT_DIR
	
	def test_default_subtitle_dir(self, config_manager: ConfigManager):
		"""Test default subtitle directory."""
		default_config = ConfigManager(config_manager.config_file)._get_default_config()
		assert default_config[ConfigKey.SUBTITLE_DIR] == ConfigDef.DEFAULT_SUBTITLE_DIR
	
	def test_default_log_dir(self, config_manager: ConfigManager):
		"""Test default log directory."""
		default_config = ConfigManager(config_manager.config_file)._get_default_config()
		assert default_config[ConfigKey.LOG_DIR] == ConfigDef.DEFAULT_LOG_DIR


# ==================== ====================
# Test Suite: Config File Operations
# ==================== ====================

class TestConfigFileOperations:
	"""Test config file loading and saving."""
	
	def test_load_existing_config(self, config_file, config_manager: ConfigManager):
		"""Test loading an existing config file."""
		config_manager.config = {"test_key": "test_value"}
		config_manager.reload()
		assert ConfigKey.FFMPEG_PATH in config_manager.config
	
	def test_create_new_config_file(self, config_file, temp_dir):
		"""Test creating a new config file when it doesn't exist."""
		original_config = {
			ConfigKey.FFMPEG_PATH: "test_ffmpeg",
			ConfigKey.CRF: 23
		}
		
		# Save manually to test file creation
		manager = ConfigManager(config_file)
		manager.config.update(original_config)
		manager._save_config()
		
		# Verify file was created
		assert Path(config_file).exists()
		
		manager.reload()
		# Verify file content
		# assert json.loads(Path(config_file).read_text(encoding='utf-8')) == original_config
		assert manager.config[ConfigKey.FFMPEG_PATH] == original_config[ConfigKey.FFMPEG_PATH]
		assert manager.config[ConfigKey.CRF] == original_config[ConfigKey.CRF]
	
	def test_create_parent_directories(self, temp_dir, config_file):
		"""Test creating parent directories when saving config."""
		grandparent = os.path.dirname(os.path.dirname(config_file))
		assert os.path.exists(grandparent)
		
		manager = ConfigManager(config_file)
		manager._save_config()
		
		assert os.path.exists(grandparent)
		assert os.path.exists(config_file)
		assert os.path.exists(os.path.dirname(config_file))


# ==================== ====================
# Test Suite: Update From Args
# ==================== ====================

class TestUpdateFromArgs:
	"""Test updating config from command-line args."""
	
	def test_updates_ffmpeg_path(self, config_manager: ConfigManager):
		"""Test updating FFmpeg path from args."""
		mock_args = MockArgs(ffmpeg="C:/ffmpeg/ffmpeg")
		config_manager.update_from_args(mock_args)
		assert config_manager.config[ConfigKey.FFMPEG_PATH] == "C:/ffmpeg/ffmpeg"
		assert config_manager.logger is not None
	
	def test_updates_ffprobe_path(self, config_manager: ConfigManager):
		"""Test updating FFprobe path from args."""
		mock_args = MockArgs(ffprobe="C:/ffmpeg/ffprobe")
		config_manager.update_from_args(mock_args)
		assert config_manager.config[ConfigKey.FFPROBE_PATH] == "C:/ffmpeg/ffprobe"
	
	def test_updates_input_directory(self, config_manager: ConfigManager):
		"""Test updating input directory from args."""
		mock_args = MockArgs(input="D:/videos")
		config_manager.update_from_args(mock_args)
		assert config_manager.config[ConfigKey.INPUT_DIR] == "D:/videos"
	
	def test_updates_output_directory(self, config_manager: ConfigManager):
		"""Test updating output directory from args."""
		mock_args = MockArgs(output="D:/encoded")
		config_manager.update_from_args(mock_args)
		assert config_manager.config[ConfigKey.OUTPUT_DIR] == "D:/encoded"
	
	def test_updates_subtitle_directory(self, config_manager: ConfigManager):
		"""Test updating subtitle directory from args."""
		mock_args = MockArgs(sub="D:/subs")
		config_manager.update_from_args(mock_args)
		assert config_manager.config[ConfigKey.SUBTITLE_DIR] == "D:/subs"
	
	def test_updates_crf_value(self, config_manager: ConfigManager):
		"""Test updating CRF value from args."""
		mock_args = MockArgs(crf=25)
		config_manager.update_from_args(mock_args)
		assert config_manager.config[ConfigKey.CRF] == 25
	
	def test_updates_volume_value(self, config_manager: ConfigManager):
		"""Test updating volume value from args."""
		mock_args = MockArgs(volume=60)
		config_manager.update_from_args(mock_args)
		assert config_manager.config[ConfigKey.VOLUME] == 60
	
	def test_updates_multiple_args(self, config_manager: ConfigManager):
		"""Test updating multiple args simultaneously."""
		mock_args = MockArgs(
			ffmpeg="C:/ffmpeg",
			ffprobe="C:/ffprobe",
			input="input",
			output="output",
			sub="subs",
			crf=24,
			volume=50
		)
		config_manager.update_from_args(mock_args)
		
		assert config_manager.config[ConfigKey.FFMPEG_PATH] == "C:/ffmpeg"
		assert config_manager.config[ConfigKey.FFPROBE_PATH] == "C:/ffprobe"
		assert config_manager.config[ConfigKey.INPUT_DIR] == "input"
		assert config_manager.config[ConfigKey.OUTPUT_DIR] == "output"
		assert config_manager.config[ConfigKey.SUBTITLE_DIR] == "subs"
		assert config_manager.config[ConfigKey.CRF] == 24
		assert config_manager.config[ConfigKey.VOLUME] == 50
	
	def test_updates_none_values_ignored(self, config_manager: ConfigManager):
		"""Test updating with None values (should be ignored)."""
		mock_args = MockArgs(ffmpeg=None, crf=None, volume=None)
		config_manager.update_from_args(mock_args)
		
		assert config_manager.config[ConfigKey.FFMPEG_PATH] is not None
		assert config_manager.config[ConfigKey.CRF] is not None
		assert config_manager.config[ConfigKey.VOLUME] is not None
	
	def test_updates_valid_string_values(self, config_manager: ConfigManager):
		"""Test updating with valid string values."""
		mock_args = MockArgs(crf="25", volume="55")
		config_manager.update_from_args(mock_args)
		
		assert config_manager.config[ConfigKey.CRF] == 25
		assert config_manager.config[ConfigKey.VOLUME] == 55


# ==================== ====================
# Test Suite: Get Configuration
# ==================== ====================

class TestGetConfiguration:
	"""Test retrieving configuration values."""
	
	def test_get_existing_key(self, config_manager: ConfigManager):
		"""Test getting an existing config key."""
		mock_args = MockArgs(crf=30)
		config_manager.update_from_args(mock_args)
		
		result = config_manager.get(ConfigKey.CRF, ConfigDef.DEFAULT_CRF)
		assert result == 30
	
	def test_get_nonexistent_key(self, config_manager: ConfigManager):
		"""Test getting a nonexistent config key."""
		result = config_manager.get(ConfigKey.FFPROBE_PATH, "default")
		assert result == ConfigDef.DEFAULT_FFPROBE  # Default from ConfigDef
	
	def test_get_with_default_param(self, config_manager: ConfigManager):
		"""Test getting with default parameter."""
		result = config_manager.get("nonexistent config key", "custom_default")
		assert result == "custom_default"


# ==================== ====================
# Test Suite: Edge Cases
# ==================== ====================

class TestEdgeCases:
	"""Test edge cases and boundary conditions."""
	
	def test_empty_config_dict(self, config_manager: ConfigManager):
		"""Test handling empty config dictionary."""
		config_manager.config = {}
		assert config_manager.get(ConfigKey.FFMPEG_PATH) is None
	
	def test_config_with_special_characters(self, config_manager: ConfigManager):
		"""Test config with special characters in paths."""
		mock_args = MockArgs(input='C:\\Users\\Test\\Videos', output='C:\\Users\\Test\\Encoded')
		config_manager.update_from_args(mock_args)
		
		assert config_manager.config[ConfigKey.INPUT_DIR] == 'C:\\Users\\Test\\Videos'
		assert config_manager.config[ConfigKey.OUTPUT_DIR] == 'C:\\Users\\Test\\Encoded'
	
	def test_config_with_noself(self, config_manager: ConfigManager):
		"""Test config with non-numeric values."""
		mock_args = MockArgs(crf="invalid", volume="not_a_number")
		config_manager.update_from_args(mock_args)
		
		assert config_manager.config[ConfigKey.CRF] == ConfigDef.DEFAULT_CRF
		assert config_manager.config[ConfigKey.VOLUME] == ConfigDef.DEFAULT_VOLUME
	
	def test_large_config_values(self, config_manager: ConfigManager):
		"""Test config with large values."""
		mock_args = MockArgs(crf=60, volume=100)
		config_manager.update_from_args(mock_args)
		
		assert config_manager.config[ConfigKey.CRF] == 60
		assert config_manager.config[ConfigKey.VOLUME] == 100
	
	def test_small_config_values(self, config_manager: ConfigManager):
		"""Test config with small values."""
		mock_args = MockArgs(crf=0, volume=1)
		config_manager.update_from_args(mock_args)
		
		assert config_manager.config[ConfigKey.CRF] == 0
		assert config_manager.config[ConfigKey.VOLUME] == 1
	
	def test_unicode_in_paths(self, config_manager: ConfigManager):
		"""Test config with unicode characters in paths."""
		mock_args = MockArgs(input='한국어 디렉토리')
		config_manager.update_from_args(mock_args)
		assert config_manager.config[ConfigKey.INPUT_DIR] == '한국어 디렉토리'


# ==================== ====================
# Test Suite: Logging
# ==================== ====================

class TestLogging:
	"""Test logging functionality."""
	
	def test_logger_initialization(self, config_manager: ConfigManager):
		"""Test logger initialization."""
		assert hasattr(config_manager, 'logger')
		assert isinstance(config_manager.logger, logging.Logger)
	
	def test_logger_info_for_load(self, config_manager, caplog):
		"""Test logger.info() for config loading."""
		with caplog.at_level(logging.DEBUG):
			config_manager.config = {"loaded": True}
			config_manager.reload()
			assert "Settings loaded" in caplog.text
	
	def test_logger_info_for_save(self, config_manager, caplog):
		"""Test logger.info() for config saving."""
		with caplog.at_level(logging.INFO):
			config_manager._save_config()
		assert "Config saved" in caplog.text
	
	def test_logger_debug_for_update(self, config_manager, caplog):
		"""Test logger.debug() for config updates."""
		mock_args = MockArgs(crf=25)
		with caplog.at_level(logging.DEBUG):
			config_manager.update_from_args(mock_args)
		assert "CRF updated" in caplog.text


# ==================== ====================
# Test Suite: Type Safety
# ==================== ====================

class TestTypeSafety:
	"""Test type safety and validation."""
	
	def test_type_hint_in_method_signature(self, config_manager: ConfigManager):
		"""Test that method signatures have proper type hints."""
		import inspect
		sig = inspect.signature(config_manager.update_from_args)
		assert 'args: argparse.Namespace' in str(sig)
	
	def test_return_type_hint(self, config_manager: ConfigManager):
		"""Test return type hint is present."""
		import inspect
		sig = inspect.signature(config_manager.get)
		assert '-> Any' in str(sig)


# ==================== ====================
# Test Suite: Integration
# ==================== ====================

class TestIntegration:
	"""Test integration between components."""
	
	def test_full_workflow_load_save_get_update(self, config_manager: ConfigManager):
		"""Test full workflow: load, save, get, update."""
		# Initial state
		initial_crf = config_manager.get(ConfigKey.CRF)
		assert initial_crf < 100
		
		# Update
		mock_args = MockArgs(crf=65)
		config_manager.update_from_args(mock_args)
		updated_crf = config_manager.config[ConfigKey.CRF]
		assert updated_crf == 65
		
		# Save
		config_manager._save_config()
		
		# Get
		restored_crf = config_manager.get(ConfigKey.CRF)
		assert restored_crf == 65
		
		# Verify file content
		file_content = json.loads(config_manager.config_file.read_text(encoding='utf-8'))
		assert file_content[ConfigKey.CRF] == 65


# ==================== ====================
# Test Suite: Error Handling
# ==================== ====================

class TestErrorHandling:
	"""Test error handling scenarios."""
	
	def test_corrupt_json_file(self, config_manager: ConfigManager):
		"""JSON 문법이 깨진 설정 파일도 백업 후 기본 설정으로 대체되어야 함."""
		
		config_manager.config_file.write_text("not valid json {{{")

		config_manager.reload()

		backup_files = list(config_manager.config_file.parent.glob(config_manager.config_file.name + ".*.bak"))
		assert len(backup_files) == 1
		assert backup_files[0].read_text(encoding='utf-8') == "not valid json {{{"
		assert isinstance(config_manager.config, dict)
		assert config_manager.config[ConfigKey.CRF] == ConfigDef.DEFAULT_CRF
	
	def test_empty_config_file(self, config_manager: ConfigManager):
		"""빈 설정 파일도 백업 후 기본 설정으로 대체되어야 함."""
		config_manager.config_file.write_text("")
		
		config_manager.reload()

		backup_files = list(config_manager.config_file.parent.glob(config_manager.config_file.name + ".*.bak"))
		assert len(backup_files) == 1
		assert backup_files[0].read_text(encoding='utf-8') == ""
		assert isinstance(config_manager.config, dict)
		assert config_manager.config[ConfigKey.CRF] == ConfigDef.DEFAULT_CRF

	def test_invalid_config_backed_up(self, config_manager: ConfigManager):
		"""객체가 아닌 설정 파일은 타임스탬프 백업으로 보관되고 기본 설정으로 대체되어야 함."""
		config_manager.config_file.write_text("[]")

		config_manager.reload()

		backup_files = list(config_manager.config_file.parent.glob(config_manager.config_file.name + ".*.bak"))
		assert len(backup_files) == 1
		assert backup_files[0].read_text(encoding='utf-8') == "[]"
		assert isinstance(config_manager.config, dict)
		assert config_manager.config[ConfigKey.FFMPEG_PATH] == ConfigDef.DEFAULT_FFMPEG

	def test_backup_keeps_previous_backups(self, config_manager: ConfigManager):
		"""손상이 반복되어도 이전 백업 파일을 덮어쓰지 않아야 함."""
		config_manager.config_file.write_text("[]")
		config_manager.reload()
		config_manager.config_file.write_text("[]")
		config_manager.reload()

		backup_files = list(config_manager.config_file.parent.glob(config_manager.config_file.name + ".*.bak"))
		assert len(backup_files) == 2
		for backup_file in backup_files:
			assert backup_file.read_text(encoding='utf-8') == "[]"

	def test_backup_name_collision_uses_sequence(self, config_manager: ConfigManager, monkeypatch):
		"""같은 시각에 백업해도 일련번호를 붙여 기존 백업을 덮어쓰지 않아야 함."""
		class FixedDatetime:
			@classmethod
			def now(cls):
				return datetime(2026, 10, 21, 10, 0, 0)

		monkeypatch.setattr("src.config.datetime", FixedDatetime)

		for _ in range(2):
			config_manager.config_file.write_text("[]")
			config_manager.reload()

		prefix = config_manager.config_file.name + ".20261021-100000"
		names = sorted(path.name for path in config_manager.config_file.parent.glob(prefix + "*.bak"))
		assert names == [prefix + "-1.bak", prefix + ".bak"]

	def test_backup_pruned_to_max(self, config_manager: ConfigManager, monkeypatch):
		"""백업은 ConfigDef.MAX_CONFIG_BACKUPS 개까지만 유지되어야 함."""
		class AdvancingDatetime:
			current = datetime(2026, 10, 21, 10, 0, 0)

			@classmethod
			def now(cls):
				value = cls.current
				cls.current = value + timedelta(seconds=1)
				return value

		monkeypatch.setattr("src.config.datetime", AdvancingDatetime)

		for _ in range(ConfigDef.MAX_CONFIG_BACKUPS + 2):
			config_manager.config_file.write_text("[]")
			config_manager.reload()

		names = sorted(path.name for path in config_manager.config_file.parent.glob(config_manager.config_file.name + ".*.bak"))
		assert len(names) == ConfigDef.MAX_CONFIG_BACKUPS
		# 가장 오래된 백업 2개는 삭제되고 최신 5개만 남아야 함
		assert names[0] == config_manager.config_file.name + ".20261021-100002.bak"

	def test_backup_protects_newest_when_same_second(self, config_manager: ConfigManager, monkeypatch):
		"""같은 초에 보관 한도를 넘겨도 방금 만든 최신 백업은 남아야 함."""
		class FixedDatetime:
			@classmethod
			def now(cls):
				return datetime(2026, 10, 21, 10, 0, 0)

		monkeypatch.setattr("src.config.datetime", FixedDatetime)

		for _ in range(ConfigDef.MAX_CONFIG_BACKUPS + 2):
			config_manager.config_file.write_text("[]")
			config_manager.reload()

		names = sorted(path.name for path in config_manager.config_file.parent.glob(config_manager.config_file.name + ".*.bak"))
		newest = f"{config_manager.config_file.name}.20261021-100000-{ConfigDef.MAX_CONFIG_BACKUPS + 1}.bak"
		assert len(names) == ConfigDef.MAX_CONFIG_BACKUPS
		assert newest in names

	def test_prune_respects_protect(self, config_manager: ConfigManager):
		"""정리 시 보호 대상으로 지정한 백업은 삭제하지 않아야 함."""
		for index in range(ConfigDef.MAX_CONFIG_BACKUPS + 1):
			backup_file = config_manager.config_file.parent / f"{config_manager.config_file.name}.20261021-1000{index:02d}.bak"
			backup_file.write_text(str(index))

		protected_file = config_manager.config_file.parent / f"{config_manager.config_file.name}.20261021-100000.bak"
		config_manager._prune_backups(protect=protected_file)

		backup_files = list(config_manager.config_file.parent.glob(config_manager.config_file.name + ".*.bak"))
		assert protected_file.exists()
		assert len(backup_files) == ConfigDef.MAX_CONFIG_BACKUPS + 1

	def test_prune_failure_does_not_break_reload(self, config_manager: ConfigManager, monkeypatch):
		"""오래된 백업 삭제가 실패해도 설정 로드는 계속되어야 함."""
		original_unlink = Path.unlink

		def failing_unlink(self, missing_ok: bool = False):
			if (self.name.endswith(".bak")):
				raise OSError("unlink failed")
			return original_unlink(self, missing_ok=missing_ok)

		monkeypatch.setattr(Path, "unlink", failing_unlink)

		for _ in range(ConfigDef.MAX_CONFIG_BACKUPS + 1):
			config_manager.config_file.write_text("[]")
			config_manager.reload()

		assert config_manager.config[ConfigKey.CRF] == ConfigDef.DEFAULT_CRF
		# 삭제에 실패했으므로 백업이 한도보다 많이 남아 있음
		backup_files = list(config_manager.config_file.parent.glob(config_manager.config_file.name + ".*.bak"))
		assert ConfigDef.MAX_CONFIG_BACKUPS < len(backup_files)

	def test_save_skipped_after_backup_failure(self, config_manager: ConfigManager, monkeypatch):
		"""백업 실패 후에는 원본을 덮어쓰지 않도록 저장을 건너뛰어야 함."""
		config_manager.config_file.write_text("[]")

		def raise_backup_error(*args, **kwargs):
			raise OSError("backup failed")

		with monkeypatch.context() as patch:
			patch.setattr("src.config.shutil.copy2", raise_backup_error)
			config_manager.reload()

		config_manager.config[ConfigKey.CRF] = 33
		config_manager._save_config()
		assert config_manager.config_file.read_text(encoding='utf-8') == "[]"

		# 정상 설정을 다시 읽으면 저장 차단이 해제되어야 함
		config_manager.config_file.write_text('{"crf": 21}')
		config_manager.reload()
		config_manager.config[ConfigKey.CRF] = 31
		config_manager._save_config()
		assert json.loads(config_manager.config_file.read_text(encoding='utf-8'))[ConfigKey.CRF] == 31

	def test_backup_failure_keeps_original(self, config_manager: ConfigManager, monkeypatch):
		"""백업 생성이 실패하면 기본 설정으로 동작하되 원본 설정 파일은 덮어쓰지 않아야 함."""
		config_manager.config_file.write_text("[]")

		def raise_backup_error(*args, **kwargs):
			raise OSError("backup failed")

		monkeypatch.setattr("src.config.shutil.copy2", raise_backup_error)

		config_manager.reload()

		assert config_manager.config_file.read_text(encoding='utf-8') == "[]"
		assert config_manager.config[ConfigKey.CRF] == ConfigDef.DEFAULT_CRF

	def test_backup_failure_strict_raises(self, config_file, monkeypatch):
		"""strict 모드에서는 백업 실패 시 예외를 전파해야 함."""
		manager = ConfigManager(config_file, strict=True)
		manager.config_file.write_text("[]")

		def raise_backup_error(*args, **kwargs):
			raise OSError("backup failed")

		monkeypatch.setattr("src.config.shutil.copy2", raise_backup_error)

		with pytest.raises(OSError):
			manager.reload()

		assert manager.config_file.read_text(encoding='utf-8') == "[]"


# ==================== ====================
# Test Suite: Configuration Keys
# ==================== ====================

class TestConfigurationKeys:
	"""Test configuration keys and values."""
	
	def test_all_expected_keys_defined(self, config_manager: ConfigManager):
		"""Test that all expected keys are defined."""
		expected_keys = [
			ConfigKey.FFMPEG_PATH, ConfigKey.FFPROBE_PATH,
			ConfigKey.INPUT_DIR, ConfigKey.OUTPUT_DIR,
			ConfigKey.SUBTITLE_DIR, ConfigKey.LOG_DIR,
			ConfigKey.CRF, ConfigKey.VOLUME, ConfigKey.AUDIO_BITRATE
		]
		
		for key in expected_keys:
			assert key in config_manager.config
	
	def test_config_structure_integrity(self, config_manager: ConfigManager):
		"""Test config structure integrity."""
		assert isinstance(config_manager.config, dict)
		assert all(isinstance(val, (str, int, float)) for val in config_manager.config.values())


# ==================== ====================
# Test Suite: ResolutionModes
# ==================== ====================

class TestResolutionModes:
	"""Test resolution mode handling."""
	
	def test_resolution_modes_values(self, config_manager: ConfigManager):
		"""Test resolution mode values."""
		modes = [
			ResolutionMode.SD.value,
			ResolutionMode.HD.value,
			ResolutionMode.FHD.value,
			ResolutionMode.UHD.value,
			ResolutionMode.UHD_8K.value
		]
		
		# 모든 모드 값은 비어있지 않은 문자열이어야 함
		for mode in modes:
			assert isinstance(mode, str) and mode

		# 기본 해상도 설정값은 정의된 모드 중 하나여야 함
		assert config_manager.config[ConfigKey.DEFAULT_RESOLUTION] in modes
	
	def test_resolution_mode_conversion(self, config_manager: ConfigManager):
		"""Test resolution mode conversion."""
		assert config_manager.config[ConfigKey.DEFAULT_RESOLUTION] == ResolutionMode.HD.value
		assert ResolutionMode.HD.value == "HD"


if __name__ == "__main__":
	pytest.main([__file__, "-v", "--cov"])
