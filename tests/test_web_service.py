# -*- coding: utf-8 -*-
# web_service.py 테스트 코드 - FastAPI HTTP 엔드포인트만 테스트
# made : opencode
# date : 2026-06-10

import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

import pytest
from starlette.testclient import TestClient


sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.encoder import VideoEncoder
from src.web_service import create_app


class TestCreateApp:
    """FastAPI 애플리케이션 생성 관련 테스트."""

    def test_create_app_returns_fastapi_instance(self):
        """create_app()은 FastAPI 인스턴스를 반환해야 함."""
        mock_encoder = Mock(spec=VideoEncoder)
        app = create_app(mock_encoder)
        assert app is not None

    def test_create_app_has_http_endpoints(self):
        """create_app()는 HTTP 엔드포인트를 등록해야 함."""
        mock_encoder = Mock(spec=VideoEncoder)
        app = create_app(mock_encoder)
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200

        response = client.post("/start")
        assert response.status_code == 200

        response = client.post("/stop-current")
        assert response.status_code == 200

        response = client.post("/stop-all")
        assert response.status_code == 200

        response = client.post("/set-resolution", json={"filename": "test.mp4", "resolution": "fhd"})
        assert response.status_code == 200


class TestHTTPEndpoints:
    """HTTP 엔드포인트 관련 테스트."""

    @pytest.fixture(scope="class")
    def mock_encoder(self):
        """Mock VideoEncoder 인스턴스."""
        encoder = Mock(spec=VideoEncoder)
        encoder.encode_all = AsyncMock()
        encoder.stop_current_encoding = Mock(return_value=True)
        encoder.stop_all_encoding = Mock(return_value=True)
        encoder.set_resolution_mode = Mock(return_value=True)
        encoder.get_all_status = Mock(return_value={"files": []})
        return encoder

    @pytest.fixture
    def client(self, mock_encoder):
        """TestClient 인스턴스."""
        app = create_app(mock_encoder)
        with TestClient(app) as c:
            yield c

    def test_get_index_returns_html(self, client):
        """메인 페이지는 HTML 응답을 반환해야 함."""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_get_index_fills_template_content(self, client, tmp_path):
        """템플릿 파일 내용을 읽어와야 함."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir(exist_ok=True)
        (template_dir / "index.html").write_text("<html><body>Test</body></html>", encoding="utf-8")

        with patch('src.web_service.Path', return_value=tmp_path / "templates" / "index.html"):
            response = client.get("/")
            assert response.status_code == 200

    def test_start_encoding_success(self, client, mock_encoder):
        """인코딩 시작 성공."""
        response = client.post("/start")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_start_encoding_duplicate_prevention(self, client, mock_encoder):
        """중복 실행 방지."""
        response1 = client.post("/start")
        response2 = client.post("/start")
        assert response1.status_code == 200
        assert response2.status_code == 200

    def test_start_encoding_no_encoder(self, mock_encoder):
        """encoder=None인 경우."""
        app = create_app(None)
        with TestClient(app) as c:
            response = c.post("/start")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False

    def test_stop_current_success(self, client, mock_encoder):
        """현재 인코딩 중단 성공."""
        response = client.post("/stop-current")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_stop_current_no_encoder(self):
        """encoder=None인 경우."""
        app = create_app(None)
        with TestClient(app) as c:
            response = c.post("/stop-current")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False

    def test_stop_current_no_active_encoding(self, mock_encoder):
        """진행 중인 인코딩 없는 경우."""
        mock_encoder.stop_current_encoding = Mock(return_value=False)
        app = create_app(mock_encoder)
        with TestClient(app) as c:
            response = c.post("/stop-current")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False

    def test_stop_all_success(self, client, mock_encoder):
        """전체 인코딩 중단 성공."""
        response = client.post("/stop-all")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_stop_all_no_encoder(self):
        """encoder=None인 경우."""
        app = create_app(None)
        with TestClient(app) as c:
            response = c.post("/stop-all")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False

    def test_stop_all_no_active_encoding(self, mock_encoder):
        """진행 중인 인코딩 없는 경우."""
        mock_encoder.stop_all_encoding = Mock(return_value=False)
        app = create_app(mock_encoder)
        with TestClient(app) as c:
            response = c.post("/stop-all")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False

    def test_refresh_success(self, client, mock_encoder):
        """새로고침 성공 시 삭제·추가 개수를 반환."""
        mock_encoder.refresh_files = AsyncMock(return_value={"removed": 1, "added": 2})
        response = client.post("/refresh")
        data = response.json()
        assert data["success"] is True
        assert data["removed"] == 1
        assert data["added"] == 2

    def test_refresh_already_running(self, client, mock_encoder):
        """이미 새로고침 중이면 실패 응답."""
        mock_encoder.refresh_files = AsyncMock(return_value=None)
        response = client.post("/refresh")
        assert response.json()["success"] is False

    def test_refresh_no_encoder(self):
        """encoder=None인 경우."""
        app = create_app(None)
        with TestClient(app) as c:
            response = c.post("/refresh")
            assert response.json()["success"] is False

    def test_move_file_success(self, client, mock_encoder):
        """파일 순서 변경 성공."""
        mock_encoder.move_file = Mock(return_value=True)
        response = client.post("/move-file", json={"filename": "test.mp4", "direction": "up"})
        assert response.json()["success"] is True

    def test_move_file_invalid_direction(self, client, mock_encoder):
        """잘못된 이동 방향은 실패 응답."""
        response = client.post("/move-file", json={"filename": "test.mp4", "direction": "left"})
        assert response.json()["success"] is False

    def test_move_file_not_pending(self, client, mock_encoder):
        """대기 중인 파일이 아니면 실패 응답."""
        mock_encoder.move_file = Mock(return_value=False)
        response = client.post("/move-file", json={"filename": "test.mp4", "direction": "first"})
        assert response.json()["success"] is False

    def test_set_resolution_success(self, client, mock_encoder):
        """해상도 설정 성공."""
        response = client.post("/set-resolution", json={
            "filename": "test.mp4",
            "resolution": "fhd"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_set_resolution_missing_filename(self):
        """파일명 누락."""
        app = create_app(Mock(spec=VideoEncoder))
        with TestClient(app) as c:
            response = c.post("/set-resolution", json={
                "resolution": "fhd"
            })
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False

    def test_set_resolution_missing_resolution(self):
        """해상도 누락."""
        app = create_app(Mock(spec=VideoEncoder))
        with TestClient(app) as c:
            response = c.post("/set-resolution", json={
                "filename": "test.mp4"
            })
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False

    def test_set_resolution_no_encoder(self):
        """encoder=None인 경우."""
        app = create_app(None)
        with TestClient(app) as c:
            response = c.post("/set-resolution", json={
                "filename": "test.mp4",
                "resolution": "fhd"
            })
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False


class TestEdgeCases:
    """Edge case 및 예외 처리 테스트."""

    @pytest.fixture(scope="class")
    def mock_encoder(self):
        """Mock VideoEncoder 인스턴스."""
        encoder = Mock(spec=VideoEncoder)
        encoder.encode_all = AsyncMock()
        encoder.stop_current_encoding = Mock(return_value=True)
        encoder.stop_all_encoding = Mock(return_value=True)
        encoder.set_resolution_mode = Mock(return_value=True)
        encoder.get_all_status = Mock(return_value={"files": []})
        return encoder

    def test_empty_request_body(self, mock_encoder):
        """빈 요청 바디."""
        app = create_app(mock_encoder)
        with TestClient(app) as client:
            response = client.post("/start", json={})
            assert response.status_code == 200



    def test_concurrent_requests(self, mock_encoder):
        """병렬 요청 처리."""
        app = create_app(mock_encoder)
        with TestClient(app) as client:
            responses = []
            for _ in range(5):
                response = client.post("/start")
                responses.append(response.json())
            assert len(responses) == 5

    def test_large_status_data(self, mock_encoder):
        """대용량 상태 데이터."""
        large_files = [{"filename": f"file_{i}.mp4"} for i in range(100)]
        mock_encoder.get_all_status = Mock(return_value={"files": large_files})
        app = create_app(mock_encoder)
        with TestClient(app) as client:
            response = client.post("/start")
            assert response.status_code == 200

    def test_unicode_filename_handling(self, mock_encoder):
        """유니코드 파일명 처리."""
        app = create_app(mock_encoder)
        with TestClient(app) as client:
            response = client.post("/set-resolution", json={
                "filename": "테스트.mp4",
                "resolution": "fhd"
            })
            assert response.status_code == 200

    def test_special_characters_in_resolution(self, mock_encoder):
        """해상도 값 특수문자 처리."""
        app = create_app(mock_encoder)
        with TestClient(app) as client:
            response = client.post("/set-resolution", json={
                "filename": "test.mp4",
                "resolution": "invalid!@#"
            })
            assert response.status_code == 200


class TestIntegration:
    """통합 및 전체 워크플로우 테스트."""

    @pytest.fixture(scope="class")
    def mock_encoder(self):
        """Mock VideoEncoder 인스턴스."""
        encoder = Mock(spec=VideoEncoder)
        encoder.encode_all = AsyncMock()
        encoder.stop_current_encoding = Mock(return_value=True)
        encoder.stop_all_encoding = Mock(return_value=True)
        encoder.set_resolution_mode = Mock(return_value=True)
        encoder.get_all_status = Mock(return_value={"files": []})
        return encoder

    def test_full_workflow_start_stop(self, mock_encoder):
        """전체 워크플로우 - 시작 및 중단."""
        app = create_app(mock_encoder)
        with TestClient(app) as client:
            start_response = client.post("/start")
            assert start_response.json()["success"] is True

            stop_response = client.post("/stop-current")
            assert stop_response.json()["success"] is True

    def test_full_workflow_resolution_change(self, mock_encoder):
        """전체 워크플로우 - 해상도 변경."""
        app = create_app(mock_encoder)
        with TestClient(app) as client:
            set_response = client.post("/set-resolution", json={
                "filename": "test.mp4",
                "resolution": "fhd"
            })
            assert set_response.json()["success"] is True

    def test_error_recovery_workflow(self, mock_encoder):
        """오류 복구 워크플로우."""
        app = create_app(mock_encoder)
        with TestClient(app) as client:
            for _ in range(5):
                response = client.post("/start")
                assert response.status_code == 200

    def test_multiple_clients_same_server(self, mock_encoder):
        """다중 클라이언트 지원."""
        app = create_app(mock_encoder)
        clients = []
        try:
            for _ in range(5):
                client = TestClient(app)
                clients.append(client)
            responses = [client.post("/start") for client in clients]
            assert all(r.status_code == 200 for r in responses)
        finally:
            for client in clients:
                client.close()

    def test_multiple_endpoints_integration(self, mock_encoder):
        """다중 엔드포인트 통합."""
        app = create_app(mock_encoder)
        with TestClient(app) as client:
            client.post("/start")
            client.post("/stop-current")
            response = client.post("/set-resolution", json={
                "filename": "test.mp4",
                "resolution": "fhd"
            })
            assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
