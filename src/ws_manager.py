# -*- coding: utf-8 -*-
# 영상 정보 관리 시스템 - WebSocket 연결 관리
# from : main.py (리팩토링 분리)

import json
from typing import Any, Dict, List

from fastapi import WebSocket, WebSocketDisconnect
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

from src.models import path_handler



class WebSocketManager:
    """WebSocket 연결을 관리하고 클라이언트에 상태를 브로드캐스트하는 클래스."""

    def __init__(self):
        """WebSocketManager의 새 인스턴스를 초기화합니다."""
        self.active_connections: List[WebSocket] = []


    async def connect(self, websocket: WebSocket) -> None:
        """WebSocket 연결을 수락하고 활성 연결 목록에 추가합니다.

        Args:
            websocket (WebSocket): 수락할 WebSocket 연결
        """
        await websocket.accept()
        self.active_connections.append(websocket)


    def disconnect(self, websocket: WebSocket) -> None:
        """활성 연결 목록에서 WebSocket 연결을 제거합니다.

        Args:
            websocket (WebSocket): 제거할 WebSocket 연결
        """
        if (websocket in self.active_connections):
            try:
                self.active_connections.remove(websocket)
            except:
                pass


    async def broadcast_all_status(self, status: Dict[str, Any]) -> None:
        """모든 활성 WebSocket 연결에 전체 파일 목록 상태를 브로드캐스트합니다.
        전송 중 오류가 발생한 연결은 자동으로 제거됩니다.

        Args:
            status (Dict[str, Any]): 전체 파일 상태를 담은 딕셔너리
        """
        disconnected = []
        for connection in self.active_connections:
            try:
                json_str = json.dumps(status, default=path_handler)
                await connection.send_json(json.loads(json_str))
            except (WebSocketDisconnect, RuntimeError, ConnectionResetError,
                    ConnectionClosedError, ConnectionClosedOK) as e:
                print(f"broadcast_all_status() WebSocket 전송 오류: {e}")
                disconnected.append(connection)
            except Exception as e:
                print(f"예상치 못한 WebSocket 오류: {e}")
                disconnected.append(connection)

        for connection in disconnected:
            self.disconnect(connection)


    async def broadcast_current_status(self, status: Dict[str, Any]) -> None:
        """모든 활성 WebSocket 연결에 현재 진행 중인 파일의 상태를 브로드캐스트합니다.
        전송 중 오류가 발생한 연결은 자동으로 제거됩니다.

        Args:
            status (Dict[str, Any]): 현재 파일 상태를 담은 딕셔너리
        """
        disconnected = []
        for connection in self.active_connections:
            try:
                json_str = json.dumps(status, default=path_handler)
                await connection.send_json(json.loads(json_str))
            except (WebSocketDisconnect, RuntimeError, ConnectionResetError,
                    ConnectionClosedError, ConnectionClosedOK) as e:
                print(f"broadcast_current_status() WebSocket 전송 오류: {e}")
                disconnected.append(connection)
            except Exception as e:
                print(f"예상치 못한 WebSocket 오류: {e}")
                disconnected.append(connection)

        for connection in disconnected:
            self.disconnect(connection)
