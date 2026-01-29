"""
ZeroMQ 기반 Daemon 클라이언트 구현

Daemon 서버에 명령어를 전송하고 결과를 받는 클라이언트입니다.
"""

import json
import zmq
from typing import Dict, Any, Optional
from uuid import uuid4
from loguru import logger


class DaemonClient:
    """ZeroMQ 기반 Daemon 클라이언트"""
    
    def __init__(self, server_address: str = "tcp://127.0.0.1:5555", timeout: int = 30):
        self.server_address = server_address
        self.timeout = timeout * 1000  # zmq timeout은 밀리초
        self.context = None
        self.socket = None
        
    def connect(self):
        """서버에 연결"""
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)  # REQ: Request socket
        self.socket.setsockopt(zmq.RCVTIMEO, self.timeout)
        self.socket.setsockopt(zmq.LINGER, 0)
        self.socket.connect(self.server_address)
        
    def close(self):
        """연결 종료"""
        if self.socket:
            self.socket.close()
        if self.context:
            self.context.term()
    
    def send_command(self, command: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        명령어를 서버로 전송하고 응답을 받습니다.
        
        Args:
            command: 실행할 명령어 이름
            params: 명령어 파라미터
            
        Returns:
            서버 응답 딕셔너리
            
        Raises:
            zmq.error.Again: 타임아웃 발생
            Exception: 다른 오류 발생
        """
        if params is None:
            params = {}
        
        request_id = uuid4().hex
        
        request = {
            "id": request_id,
            "command": command,
            "params": params
        }
        
        try:
            # 요청 전송
            self.socket.send_string(json.dumps(request))
            logger.debug(f"명령어 전송: {command} with params: {params}")
            
            # 응답 수신
            response_str = self.socket.recv_string()
            response = json.loads(response_str)
            logger.debug(f"응답 수신: {response}")
            
            if response.get("id") != request_id:
                raise ValueError(f"Response ID mismatch: expected {request_id}, got {response.get('id')}")
            
            return response
            
        except zmq.error.Again:
            raise TimeoutError(f"Daemon 서버 응답 시간 초과 ({self.timeout // 1000}초)")
        except json.JSONDecodeError as e:
            raise ValueError(f"서버 응답 JSON 파싱 오류: {e}")
    
    def execute(self, command: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        명령어를 실행하고 결과만 반환합니다.
        
        Args:
            command: 실행할 명령어 이름
            params: 명령어 파라미터
            
        Returns:
            명령어 실행 결과 데이터
            
        Raises:
            RuntimeError: 명령어 실행 실패
        """
        response = self.send_command(command, params)
        
        if response.get("status") == "error":
            error = response.get("error", "Unknown error")
            raise RuntimeError(f"명령어 실행 실패: {error}")
        
        return response.get("data")
    
    def __enter__(self):
        """Context manager 진입"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager 종료"""
        self.close()


def create_client(server_address: str = "tcp://127.0.0.1:5555", timeout: int = 30) -> DaemonClient:
    """
    Daemon 클라이언트를 생성하고 연결합니다.
    
    Args:
        server_address: 서버 주소
        timeout: 타임아웃 (초)
        
    Returns:
        연결된 Daemon 클라이언트
    """
    client = DaemonClient(server_address, timeout)
    client.connect()
    return client

