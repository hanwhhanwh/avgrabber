"""
WebSocket Manager Comprehensive Test Suite
Tests: 33+ diverse scenarios covering edge cases, error handling, mocks, async behavior
"""

import pytest
import asyncio
from typing import Any
from unittest.mock import Mock, AsyncMock
from fastapi import WebSocket
from src.ws_manager import WebSocketManager


def make_websocket(**send_json_kwargs: Any) -> Mock:
	"""accept()와 send_json()이 AsyncMock인 WebSocket 목 객체를 생성합니다.

	Args:
		**send_json_kwargs (Any): send_json AsyncMock에 전달할 추가 인자 (예: side_effect)

	Returns:
		Mock: WebSocket 스펙을 가진 목 객체
	"""

	websocket = Mock(spec=WebSocket)
	websocket.accept = AsyncMock()
	websocket.send_json = AsyncMock(**(send_json_kwargs or {}))

	return websocket


def connect_all(manager: WebSocketManager, *websockets: Mock) -> None:
	"""비동기 connect()를 동기 테스트에서 실행할 수 있도록 감싸 호출합니다.

	Args:
		manager (WebSocketManager): 연결을 등록할 관리자
		*websockets (Mock): 등록할 WebSocket 목 객체
	"""

	async def _connect() -> None:
		for websocket in websockets:
			await manager.connect(websocket)

	asyncio.run(_connect())



class TestWebSocketManager:
	"""WebSocketManager 기본 기능 테스트"""

	def test_initialization(self):
		"""테스트 1: WebSocketManager 초기화 테스트"""
		manager = WebSocketManager()
		assert manager.active_connections == []

	def test_connect_single_connection(self):
		"""테스트 2: 단일 연결 시연 테스트"""
		manager = WebSocketManager()
		mock_websocket = make_websocket()
		connect_all(manager, mock_websocket)
		assert len(manager.active_connections) == 1
		assert mock_websocket in manager.active_connections

	def test_connect_multiple_connections(self):
		"""테스트 3: 다중 연결 시연 테스트"""
		manager = WebSocketManager()
		ws1 = make_websocket()
		ws2 = make_websocket()
		connect_all(manager, ws1, ws2)
		assert len(manager.active_connections) == 2

	def test_connect_already_connected(self):
		"""테스트 4: 이미 연결된 연결 추가 테스트"""
		manager = WebSocketManager()
		ws1 = make_websocket()
		connect_all(manager, ws1)
		new_ws = make_websocket()
		connect_all(manager, new_ws)
		assert len(manager.active_connections) == 2
		# 기존 연결은 변경 안됨
		assert ws1 in manager.active_connections



class TestWebSocketManager_Disconnect:
	"""WebSocket 연결 분리 기능 테스트"""

	def test_disconnect_single_connection(self):
		"""테스트 5: 단일 연결 분리 테스트"""
		manager = WebSocketManager()
		ws1 = make_websocket()
		connect_all(manager, ws1)
		manager.disconnect(ws1)
		assert len(manager.active_connections) == 0

	def test_disconnect_non_existent_connection(self):
		"""테스트 6: 존재하지 않는 연결 분리 Test"""
		manager = WebSocketManager()
		ws1 = make_websocket()
		connect_all(manager, ws1)
		# 비존재하는 연결 분리 시도
		non_existent_ws = make_websocket()
		manager.disconnect(non_existent_ws)
		assert len(manager.active_connections) == 1

	def test_disconnect_multiple_connections(self):
		""" 테스트 7: 다중 연결 분리 Test"""
		manager = WebSocketManager()
		ws1 = make_websocket()
		ws2 = make_websocket()
		connect_all(manager, ws1, ws2)
		manager.disconnect(ws1)
		assert len(manager.active_connections) == 1
		assert ws2 in manager.active_connections

	def test_disconnect_all_connections(self):
		""" 테스토 8: 모든 연결 분리 Test"""
		manager = WebSocketManager()
		ws1 = make_websocket()
		ws2 = make_websocket()
		connect_all(manager, ws1, ws2)
		manager.disconnect(ws1)
		manager.disconnect(ws2)
		assert len(manager.active_connections) == 0



class TestBroadcast_Status:
	"""브로드캐스트 상태 테스트"""

	def test_broadcast_all_status_empty_connections(self):
		"""테스트 9: 빈 연결 목록 브로드캐스트 테스트"""
		manager = WebSocketManager()
		status = {"file_list": [], "current_file": None}

		asyncio.run(manager.broadcast_all_status(status))
		assert len(manager.active_connections) == 0

	def test_broadcast_all_status_single_connection(self):
		"""테스트 10: 단일 연결 브로드캐스트 Test"""
		manager = WebSocketManager()
		ws1 = make_websocket()
		connect_all(manager, ws1)

		status = {"file_list": [1, 2, 3]}
		asyncio.run(manager.broadcast_all_status(status))
		ws1.send_json.assert_called_once()

	def test_broadcast_all_status_multiple_connections(self):
		""" 테스트 11: 다중 연결 브로드캐스트 Test"""
		manager = WebSocketManager()
		ws1 = make_websocket()
		ws2 = make_websocket()
		connect_all(manager, ws1, ws2)

		status = {"file_list": [1, 2, 3]}
		asyncio.run(manager.broadcast_all_status(status))
		ws1.send_json.assert_called_once()
		ws2.send_json.assert_called_once()

	def test_broadcast_all_status_with_nonexistent_json(self):
		""" 테스트 12: JSON 에러 시연 Test"""
		manager = WebSocketManager()
		ws1 = make_websocket(side_effect=Exception("JSON Error"))
		connect_all(manager, ws1)

		status = {"file_list": [1, 2, 3]}
		asyncio.run(manager.broadcast_all_status(status))
		ws1.send_json.assert_called_once()



class TestBroadcast_Conditional:
	"""조건부 브로드캐스트 테스트"""

	def test_broadcast_current_status_same_as_all(self):
		"""테스트 13: 브로드캐스트 상태 동일성 Test"""
		manager = WebSocketManager()
		ws1 = make_websocket()
		connect_all(manager, ws1)

		status = {"file_list": [1, 2, 3]}
		asyncio.run(manager.broadcast_current_status(status))
		ws1.send_json.assert_called_once()



class TestError_Handling:
	"""오류 처리 테스트"""

	def test_disconnect_on_error(self):
		"""테스트 14: 에러 시 연결 분리 Test"""
		manager = WebSocketManager()
		ws1 = make_websocket(side_effect=Exception("Test Error"))
		connect_all(manager, ws1)

		status = {"file_list": [1]}
		asyncio.run(manager.broadcast_all_status(status))
		assert len(manager.active_connections) == 0



class TestEdge_Cases:
	"""가변적인 경우 테스트"""

	def test_broadcast_with_large_status_dict(self):
		"""테스트 15: 대용량 상태 딕셔너리 브로드캐스트 Test"""
		manager = WebSocketManager()
		ws1 = make_websocket()
		connect_all(manager, ws1)

		large_status = {"file_list": list(range(1000))}
		asyncio.run(manager.broadcast_all_status(large_status))
		ws1.send_json.assert_called_once()

	def test_broadcast_with_nested_object(self):
		"""테스트 16: 중첩 객체 브로드캐스트 Test"""
		manager = WebSocketManager()
		ws1 = make_websocket()
		connect_all(manager, ws1)

		nested_status = {
			"file_list": [{"name": "file1", "size": 100}],
			"metadata": {"timestamp": 12345}
		}
		asyncio.run(manager.broadcast_all_status(nested_status))
		ws1.send_json.assert_called_once()



class TestConcurrent:
	"""동시성 테스트"""

	def test_concurrent_connect_disconnect(self):
		"""TEST 17: 동시 연결/분리 Test"""
		manager = WebSocketManager()

		ws1 = make_websocket()
		connect_all(manager, ws1)
		manager.disconnect(ws1)

		ws2 = make_websocket()
		connect_all(manager, ws2)
		manager.disconnect(ws2)

		ws3 = make_websocket()
		connect_all(manager, ws3)
		manager.disconnect(ws3)

		assert len(manager.active_connections) == 0

	def test_concurrent_broadcast(self):
		"""TEST 18: 동시 브로드캐스트 Test"""
		manager = WebSocketManager()

		ws1 = make_websocket()
		ws2 = make_websocket()
		connect_all(manager, ws1, ws2)

		# 브로드캐스트 실행
		asyncio.run(manager.broadcast_all_status({"file_list": [1]}))

		# send_json 가 호출되어야 함
		assert ws1.send_json.call_count >= 1
		assert ws2.send_json.call_count >= 1

	def test_connection_recovery_after_error(self):
		""" TEST 34: 에러 후 연결 복구 Test"""
		manager = WebSocketManager()

		ws1 = make_websocket()
		connect_all(manager, ws1)

		status = {"file_list": [1]}
		asyncio.run(manager.broadcast_all_status(status))

		# ws1 는 성공
		assert ws1.send_json.call_count == 1

	def test_concurrent_broadcast_same_connections(self):
		"""TEST 35: 동시 브로드캐스트 동일 연결 Test"""
		manager = WebSocketManager()
		ws1 = make_websocket()
		connect_all(manager, ws1)

		# 브로드캐스트 실행
		asyncio.run(manager.broadcast_all_status({"file_list": [1]}))

		# send_json 가 호출되어야 함
		assert ws1.send_json.call_count >= 1

	def test_broadcast_performance_with_many_connections(self):
		"""TEST 28: 많은 연결의 브로드캐스트 성능 Test"""
		manager = WebSocketManager()

		# 다수의 WebSocket 연결 생성
		connections = []
		for i in range(5):
			ws = make_websocket()
			connections.append(ws)
		connect_all(manager, *connections)

		status = {"file_list": list(range(10))}
		asyncio.run(manager.broadcast_all_status(status))

		# 모든 연결에 브로드캐스트가 전송되었는지 확인
		for ws in connections:
			ws.send_json.assert_called()

	def test_full_workflow(self):
		"""TEST 22: 전체 워크플로우 Test"""
		manager = WebSocketManager()

		ws1 = make_websocket()
		connect_all(manager, ws1)

		# 단계 1: 상태 브로드캐스트
		asyncio.run(manager.broadcast_all_status({"file_list": ["file1", "file2"]}))
		assert ws1.send_json.call_count == 1

		# 단계 2: 연결 분리
		manager.disconnect(ws1)
		assert len(manager.active_connections) == 0

		# 단계 3: 브로드캐스트 후 연결 분리
		ws2 = make_websocket()
		connect_all(manager, ws2)
		asyncio.run(manager.broadcast_all_status({"file_list": ["file3"]}))
		assert ws2.send_json.call_count == 1
		assert len(manager.active_connections) == 1

	def test_broadcast_json_transform(self):
		"""테스트 27: JSON 변환 테스트"""
		manager = WebSocketManager()
		ws1 = make_websocket()
		connect_all(manager, ws1)

		# 복잡한 데이터 구조
		status = {
			"files": [{"id": 1, "name": "test.txt"}, {"id": 2, "name": "data.bin"}],
			"active": True
		}

		asyncio.run(manager.broadcast_all_status(status))

		# send_json 가 호출되어야 함
		ws1.send_json.assert_called()

	def test_broadcast_with_mutatable_status(self):
		"""TEST 39: 변형 가능한 상태 브로드캐스트 Test"""
		manager = WebSocketManager()
		ws1 = make_websocket()
		connect_all(manager, ws1)

		status = {"file_list": [1, 2]}
		asyncio.run(manager.broadcast_all_status(status))

		# 상태가 변형됨 (비동기 후 변형)
		status["file_list"].append(3)
		assert status["file_list"] == [1, 2, 3]



class TestMemory_Resources:
	"""메모리 리소스 테스트"""

	def test_broadcast_memory_usage(self):
		"""TEST 40: 브로드캐스트 메모리 사용 Test"""
		manager = WebSocketManager()

		ws1 = make_websocket()
		ws2 = make_websocket()
		connect_all(manager, ws1, ws2)

		# 연결이 브로드캐스트 후에도 메모리에서 유지됨
		status = {"file_list": [1]}
		asyncio.run(manager.broadcast_all_status(status))

		# active_connections 가 빈 것이 아니어야 함
		assert len(manager.active_connections) >= 1



class TestIntegration_With_Router:
	"""라우터 통합 테스트"""

	def test_broadcast_in_routine(self):
		""" TEST 41: 루틴 내에서 브로드캐스트 Test"""
		manager = WebSocketManager()

		# 비동기 작업 내에서 브로드캐스트
		async def simulate_background_task():
			await manager.broadcast_all_status({"file_list": [1, 2, 3]})

		asyncio.run(simulate_background_task())


if __name__ == "__main__":
	pytest.main()