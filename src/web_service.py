# -*- coding: utf-8 -*-
# 영상 정보 관리 시스템 - 웹 인터페이스 (FastAPI 라우트)
# from : main.py (리팩토링 분리)

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

from src.encoder import VideoEncoder
from src.models import ConfigDef, ConfigKey, MoveDirection
from src.ws_manager import WebSocketManager



def create_app(encoder: VideoEncoder) -> FastAPI:
    """FastAPI 애플리케이션을 생성하고 라우트를 등록합니다.

    Args:
        encoder (VideoEncoder): VideoEncoder 인스턴스

    Returns:
        FastAPI: 라우트와 정적 파일 마운트가 완료된 FastAPI 앱
    """
    websocket_manager = WebSocketManager()
    encoding_task: Optional[asyncio.Task] = None

    app = FastAPI()
    app.mount("/css", StaticFiles(directory="templates/css"), name="css")
    app.mount("/js", StaticFiles(directory="templates/js"), name="js")


    @app.get("/")
    async def get_index() -> HTMLResponse:
        """메인 페이지(templates/index.html)를 반환합니다."""
        template_file = Path("templates/index.html")

        with open(template_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)


    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        """WebSocket 엔드포인트. 연결 시 전체 상태를 전송하고 keepalive ping을 유지합니다."""
        await websocket_manager.connect(websocket)

        try:
            if (encoder is not None):
                await websocket.send_json(encoder.get_all_status())
        except Exception as e:
            print(f"websocket_endpoint send_json() error: {e}")
            print(f"{encoder.get_all_status()=}")

        async def _keepalive_ping() -> None:
            """10초 간격으로 ping 메시지를 전송하여 WebSocket 연결을 유지합니다."""
            try:
                while True:
                    await asyncio.sleep(10)
                    try:
                        await websocket.send_json({"type": "ping"})
                    except (WebSocketDisconnect, ConnectionClosedError, ConnectionClosedOK):
                        break
                    except Exception:
                        break
            except asyncio.CancelledError:
                pass

        ping_task = asyncio.create_task(_keepalive_ping())

        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            websocket_manager.disconnect(websocket)
        except (ConnectionClosedError, ConnectionClosedOK):
            websocket_manager.disconnect(websocket)
        finally:
            ping_task.cancel()
            await asyncio.gather(ping_task, return_exceptions=True)


    @app.post("/start")
    async def start_encoding() -> Dict[str, Any]:
        """인코딩을 시작합니다. 이미 진행 중인 경우 중복 실행을 방지합니다."""
        nonlocal encoding_task

        if (encoding_task is not None and not encoding_task.done()):
            return {"success": False, "message": "이미 인코딩이 진행 중입니다"}

        if (encoder is None):
            return {"success": False, "message": "인코더가 초기화되지 않았습니다"}

        encoding_task = asyncio.create_task(encoder.encode_all(websocket_manager))
        return {"success": True, "message": "인코딩을 시작했습니다"}


    @app.post("/stop-current")
    async def stop_current_encoding() -> Dict[str, Any]:
        """현재 진행 중인 파일의 인코딩을 중단합니다."""
        if (encoder is None):
            return {"success": False, "message": "인코더가 초기화되지 않았습니다"}

        if (encoder.stop_current_encoding()):
            return {"success": True, "message": "현재 파일 인코딩을 중단합니다"}
        else:
            return {"success": False, "message": "진행 중인 인코딩이 없습니다"}


    @app.post("/stop-all")
    async def stop_all_encoding() -> Dict[str, Any]:
        """모든 인코딩 작업을 중단합니다."""
        if (encoder is None):
            return {"success": False, "message": "인코더가 초기화되지 않았습니다"}

        if (encoder.stop_all_encoding()):
            return {"success": True, "message": "전체 인코딩을 중단합니다"}
        else:
            return {"success": False, "message": "진행 중인 인코딩이 없습니다"}


    @app.post("/refresh")
    async def refresh_files() -> Dict[str, Any]:
        """
        입력 디렉토리를 다시 읽어 삭제된 파일은 제거하고 신규 파일은 목록 끝에 추가합니다.
        """
        if (encoder is None):
            return {"success": False, "message": "인코더가 초기화되지 않았습니다"}

        result = await encoder.refresh_files(websocket_manager)
        if (result is None):
            return {"success": False, "message": "이미 새로고침 중입니다"}

        await websocket_manager.broadcast_all_status(encoder.get_all_status())
        return {"success": True, "message": f"삭제 {result['removed']}개, 추가 {result['added']}개", **result}


    @app.post("/move-file")
    async def move_file(data: Dict[str, str]) -> Dict[str, Any]:
        """
        대기 중인 파일의 목록 내 위치(인코딩 순서)를 이동합니다.

        Args:
            data (Dict[str, str]): {"filename": "파일명", "direction": "first|up|down|last"} 형식의 요청 데이터

        Returns:
            Dict[str, Any]: 성공 여부와 메시지를 포함한 딕셔너리
        """
        if (encoder is None):
            return {"success": False, "message": "인코더가 초기화되지 않았습니다"}

        try:
            direction = MoveDirection(data.get("direction"))
        except ValueError:
            return {"success": False, "message": "이동 방향이 올바르지 않습니다"}

        if (encoder.move_file(data.get("filename"), direction)):
            await websocket_manager.broadcast_all_status(encoder.get_all_status())
            return {"success": True, "message": "파일 순서를 변경했습니다"}
        else:
            return {"success": False, "message": "대기 중인 파일을 찾을 수 없습니다"}


    @app.post("/set-resolution")
    async def set_resolution(data: Dict[str, str]) -> Dict[str, Any]:
        """특정 파일의 해상도 모드를 변경합니다.

        Args:
            data (Dict[str, str]): {"filename": "파일명", "resolution": "hd|fhd"} 형식의 요청 데이터

        Returns:
            Dict[str, Any]: 성공 여부와 메시지를 포함한 딕셔너리
        """
        if (encoder is None):
            return {"success": False, "message": "인코더가 초기화되지 않았습니다"}

        filename = data.get("filename")
        resolution = data.get("resolution")

        if (not filename or not resolution):
            return {"success": False, "message": "파일명과 해상도를 지정해야 합니다"}

        if (encoder.set_resolution_mode(filename, resolution)):
            await websocket_manager.broadcast_all_status(encoder.get_all_status())
            return {"success": True, "message": "해상도 모드를 변경했습니다"}
        else:
            return {"success": False, "message": "파일을 찾을 수 없습니다"}


    @app.get("/settings")
    async def get_settings() -> Dict[str, Any]:
        """현재 기본 설정(conf/encode.json)을 반환합니다."""
        if (encoder is None):
            return {"success": False, "message": "인코더가 초기화되지 않았습니다"}

        return {"success": True, "settings": encoder.config.get_all()}


    @app.put("/settings")
    async def update_settings(data: Dict[str, Any]) -> Dict[str, Any]:
        """기본 설정을 검증·저장하고 실행 중인 인코더에 즉시 반영합니다.

        Args:
            data (Dict[str, Any]): 변경할 설정 키와 값

        Returns:
            Dict[str, Any]: 성공 여부, 저장된 설정, 키별 오류 메시지를 담은 딕셔너리
        """
        if (encoder is None):
            return {"success": False, "message": "인코더가 초기화되지 않았습니다"}

        applied, errors = encoder.config.validate_updates(data)
        if (errors):
            return {"success": False, "message": "설정 값을 확인하세요", "errors": errors}
        if (not applied):
            return {"success": False, "message": "변경할 설정이 없습니다"}

        previous_input_dir = encoder.config.get(ConfigKey.INPUT_DIR)
        previous_resolution = encoder.config.get(ConfigKey.DEFAULT_RESOLUTION)
        previous_search_subfolders = encoder.config.get(
            ConfigKey.SEARCH_SUBFOLDERS, ConfigDef.DEFAULT_SEARCH_SUBFOLDERS
        )
        if (not encoder.config.update_values(applied)):
            return {"success": False, "message": "설정을 저장하지 못했습니다 (설정 백업 실패)"}

        # 기본 해상도가 실제로 바뀐 경우에만 대기 파일의 해상도·출력 파일명을 다시 계산한다.
        resolution_changed = (
            (ConfigKey.DEFAULT_RESOLUTION in applied)
            and (str(previous_resolution).upper() != str(applied[ConfigKey.DEFAULT_RESOLUTION]).upper())
        )
        encoder.apply_settings(apply_resolution=resolution_changed)

        # 입력 디렉토리나 하위 폴더 검색 옵션이 바뀌면 파일 목록을 다시 읽는다.
        input_dir_changed = (
            (ConfigKey.INPUT_DIR in applied)
            and (applied[ConfigKey.INPUT_DIR] != previous_input_dir)
        )
        search_subfolders_changed = (
            (ConfigKey.SEARCH_SUBFOLDERS in applied)
            and (bool(applied[ConfigKey.SEARCH_SUBFOLDERS]) != bool(previous_search_subfolders))
        )
        refresh_pending = (input_dir_changed or search_subfolders_changed)

        # 파일 검색이 오래 걸려도 저장 여부를 바로 알 수 있도록 먼저 알린다.
        await websocket_manager.broadcast_message({
            "type": "settings_saved",
            "refresh_pending": refresh_pending,
            "encode_settings": encoder.get_encode_settings()
        })

        if (refresh_pending):
            await encoder.refresh_files(websocket_manager)

        await websocket_manager.broadcast_all_status(encoder.get_all_status())
        return {
            "success": True,
            "message": "설정을 저장했습니다",
            "refresh_pending": refresh_pending,
            "settings": encoder.config.get_all()
        }


    @app.post("/reencode")
    async def reencode_file(data: Dict[str, str]) -> Dict[str, Any]:
        """완료된 파일을 대기 상태로 되돌리고, 인코딩 중이 아니면 바로 다시 인코딩합니다.

        Args:
            data (Dict[str, str]): {"filename": "파일명"} 형식의 요청 데이터

        Returns:
            Dict[str, Any]: 성공 여부, 재인코딩 시작 여부, 메시지를 담은 딕셔너리
        """
        nonlocal encoding_task

        if (encoder is None):
            return {"success": False, "message": "인코더가 초기화되지 않았습니다"}

        filename = data.get("filename")
        if (not filename):
            return {"success": False, "message": "파일명을 지정해야 합니다"}

        if (not encoder.requeue_file(filename)):
            return {"success": False, "message": "완료된 파일을 찾을 수 없습니다"}

        await websocket_manager.broadcast_all_status(encoder.get_all_status())

        started = (encoding_task is None or encoding_task.done())
        if (started):
            encoding_task = asyncio.create_task(encoder.encode_all(websocket_manager))

        message = "재인코딩을 시작했습니다" if (started) else "재인코딩 대기열에 추가했습니다"
        return {"success": True, "started": started, "message": message}


    return app
