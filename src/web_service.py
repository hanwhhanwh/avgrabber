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


    return app
