"""
PNS AI Hub SDK for Python
=========================

AI Hub 서비스 API를 쉽게 사용할 수 있는 Python SDK

설치:
    pip install requests pycryptodome

사용법:
    from pns_ai import AIClient

    client = AIClient(
        api_key="pns_sk_live_xxx",
        encryption_key="your_encryption_key"
    )

    # 간단한 채팅
    response = client.chat("안녕하세요")
    print(response.text)

    # 스트리밍
    for chunk in client.chat_stream("긴 답변을 요청합니다"):
        print(chunk, end="", flush=True)
"""

import json
import base64
import requests
from typing import Optional, Iterator, Dict, Any, List
from dataclasses import dataclass

# AES 암호화를 위한 라이브러리
try:
    from Crypto.Cipher import AES
    from Crypto.Random import get_random_bytes
    CRYPTO_AVAILABLE = True
except ImportError:
    try:
        from Cryptodome.Cipher import AES
        from Cryptodome.Random import get_random_bytes
        CRYPTO_AVAILABLE = True
    except ImportError:
        CRYPTO_AVAILABLE = False


__version__ = "1.0.0"
__author__ = "PNS Lab"


class AIException(Exception):
    """AI Hub API 에러"""
    def __init__(self, message: str, code: str = None, status_code: int = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


class AuthenticationError(AIException):
    """인증 에러"""
    pass


class RateLimitError(AIException):
    """Rate limit 에러"""
    pass


class TokenLimitError(AIException):
    """토큰 한도 초과 에러"""
    pass


@dataclass
class Usage:
    """토큰 사용량"""
    input_tokens: int
    output_tokens: int
    total_tokens: int


@dataclass
class ChatResponse:
    """채팅 응답"""
    text: str
    model: str
    usage: Usage

    def __str__(self):
        return self.text


class Encryption:
    """AES-256-GCM 암호화 헬퍼"""

    @staticmethod
    def encrypt(data: Any, key: str) -> Dict[str, str]:
        """데이터를 AES-256-GCM으로 암호화"""
        if not CRYPTO_AVAILABLE:
            raise ImportError("pycryptodome 또는 pycryptodomex가 필요합니다. pip install pycryptodome")

        key_bytes = bytes.fromhex(key)
        if len(key_bytes) != 32:
            raise ValueError("암호화 키는 32바이트(64자 hex)여야 합니다")

        iv = get_random_bytes(16)
        cipher = AES.new(key_bytes, AES.MODE_GCM, nonce=iv)

        plaintext = json.dumps(data) if isinstance(data, (dict, list)) else str(data)
        ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode('utf-8'))

        return {
            "encrypted": base64.b64encode(ciphertext).decode('utf-8'),
            "iv": base64.b64encode(iv).decode('utf-8'),
            "tag": base64.b64encode(tag).decode('utf-8')
        }

    @staticmethod
    def decrypt(encrypted: str, iv: str, tag: str, key: str) -> str:
        """AES-256-GCM으로 암호화된 데이터 복호화"""
        if not CRYPTO_AVAILABLE:
            raise ImportError("pycryptodome 또는 pycryptodomex가 필요합니다. pip install pycryptodome")

        key_bytes = bytes.fromhex(key)
        iv_bytes = base64.b64decode(iv)
        tag_bytes = base64.b64decode(tag)
        ciphertext = base64.b64decode(encrypted)

        cipher = AES.new(key_bytes, AES.MODE_GCM, nonce=iv_bytes)
        plaintext = cipher.decrypt_and_verify(ciphertext, tag_bytes)

        return plaintext.decode('utf-8')


class AIClient:
    """
    PNS AI Hub 클라이언트

    Args:
        api_key: API 키 (pns_sk_live_xxx 형식)
        encryption_key: 암호화 키 (64자 hex 문자열)
        base_url: API 기본 URL (기본값: https://api.pns-lab.com)
        timeout: 요청 타임아웃 (초, 기본값: 120)

    Example:
        >>> client = AIClient(
        ...     api_key="pns_sk_live_xxx",
        ...     encryption_key="your_64_char_hex_key"
        ... )
        >>> response = client.chat("안녕하세요")
        >>> print(response.text)
    """

    DEFAULT_BASE_URL = "https://api.pns-lab.com"
    DEFAULT_TIMEOUT = 120

    def __init__(
        self,
        api_key: str,
        encryption_key: str,
        base_url: str = None,
        timeout: int = None
    ):
        if not api_key:
            raise ValueError("api_key는 필수입니다")
        if not encryption_key:
            raise ValueError("encryption_key는 필수입니다")
        if not api_key.startswith("pns_sk_"):
            raise ValueError("올바른 API 키 형식이 아닙니다 (pns_sk_live_xxx)")
        if len(encryption_key) != 64:
            raise ValueError("encryption_key는 64자 hex 문자열이어야 합니다")

        self.api_key = api_key
        self.encryption_key = encryption_key
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip('/')
        self.timeout = timeout or self.DEFAULT_TIMEOUT

        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": f"PNS-AI-SDK-Python/{__version__}"
        })

    def _handle_error(self, response: requests.Response):
        """API 에러 처리"""
        try:
            data = response.json()
            error_code = data.get("error", "unknown_error")
            message = data.get("message", "알 수 없는 오류가 발생했습니다")
        except:
            error_code = "unknown_error"
            message = response.text or "알 수 없는 오류가 발생했습니다"

        if response.status_code == 401:
            raise AuthenticationError(message, error_code, response.status_code)
        elif response.status_code == 429:
            if "token" in error_code.lower():
                raise TokenLimitError(message, error_code, response.status_code)
            raise RateLimitError(message, error_code, response.status_code)
        else:
            raise AIException(message, error_code, response.status_code)

    def chat(
        self,
        message: str,
        model: str = "claude-sonnet-4.5",
        max_tokens: int = 1024,
        temperature: float = 0.7,
        system: str = None
    ) -> ChatResponse:
        """
        AI와 채팅

        Args:
            message: 사용자 메시지
            model: 사용할 모델 (claude-sonnet-4.5, nova-lite)
            max_tokens: 최대 응답 토큰 수
            temperature: 창의성 (0.0 ~ 1.0)
            system: 시스템 프롬프트 (선택)

        Returns:
            ChatResponse: AI 응답

        Example:
            >>> response = client.chat("파이썬이 뭐야?")
            >>> print(response.text)
            >>> print(f"사용 토큰: {response.usage.total_tokens}")
        """
        # 요청 데이터 준비
        request_data = {
            "message": message,
            "model": model,
            "maxTokens": max_tokens,
            "temperature": temperature
        }
        if system:
            request_data["system"] = system

        # 암호화
        encrypted_request = Encryption.encrypt(request_data, self.encryption_key)

        # API 호출
        response = self._session.post(
            f"{self.base_url}/api/v1/chat",
            json=encrypted_request,
            timeout=self.timeout
        )

        if not response.ok:
            self._handle_error(response)

        data = response.json()

        # 응답 복호화
        decrypted = Encryption.decrypt(
            data["encrypted"],
            data["iv"],
            data["tag"],
            self.encryption_key
        )
        result = json.loads(decrypted)

        # 사용량 정보
        usage_data = data.get("usage", {})
        usage = Usage(
            input_tokens=usage_data.get("inputTokens", 0),
            output_tokens=usage_data.get("outputTokens", 0),
            total_tokens=usage_data.get("totalTokens", 0)
        )

        return ChatResponse(
            text=result.get("response", ""),
            model=result.get("model", model),
            usage=usage
        )

    def chat_stream(
        self,
        message: str,
        model: str = "claude-sonnet-4.5",
        max_tokens: int = 1024,
        temperature: float = 0.7,
        system: str = None
    ) -> Iterator[str]:
        """
        AI와 스트리밍 채팅

        Args:
            message: 사용자 메시지
            model: 사용할 모델
            max_tokens: 최대 응답 토큰 수
            temperature: 창의성
            system: 시스템 프롬프트

        Yields:
            str: 응답 텍스트 청크

        Example:
            >>> for chunk in client.chat_stream("긴 이야기를 해줘"):
            ...     print(chunk, end="", flush=True)
        """
        # 요청 데이터 준비 및 암호화
        request_data = {
            "message": message,
            "model": model,
            "maxTokens": max_tokens,
            "temperature": temperature
        }
        if system:
            request_data["system"] = system

        encrypted_request = Encryption.encrypt(request_data, self.encryption_key)

        # 스트리밍 API 호출
        response = self._session.post(
            f"{self.base_url}/api/v1/chat/stream",
            json=encrypted_request,
            timeout=self.timeout,
            stream=True
        )

        if not response.ok:
            self._handle_error(response)

        # SSE 파싱
        for line in response.iter_lines():
            if not line:
                continue

            line_str = line.decode('utf-8')
            if not line_str.startswith('data: '):
                continue

            try:
                data = json.loads(line_str[6:])

                if data.get("type") == "chunk":
                    # 청크 복호화
                    decrypted = Encryption.decrypt(
                        data["encrypted"],
                        data["iv"],
                        data["tag"],
                        self.encryption_key
                    )
                    chunk_data = json.loads(decrypted)
                    yield chunk_data.get("text", "")

                elif data.get("type") == "error":
                    raise AIException(data.get("error", "스트리밍 오류"))

                elif data.get("type") == "done":
                    break

            except json.JSONDecodeError:
                continue

    def get_models(self) -> List[Dict[str, Any]]:
        """
        사용 가능한 모델 목록 조회

        Returns:
            List[Dict]: 모델 목록

        Example:
            >>> models = client.get_models()
            >>> for model in models:
            ...     print(f"{model['id']}: {model['name']}")
        """
        response = self._session.get(
            f"{self.base_url}/api/v1/models",
            timeout=self.timeout
        )

        if not response.ok:
            self._handle_error(response)

        return response.json().get("models", [])

    def get_usage(self) -> Dict[str, Any]:
        """
        현재 사용량 조회

        Returns:
            Dict: 사용량 정보

        Example:
            >>> usage = client.get_usage()
            >>> print(f"이번 달 사용: {usage['currentMonthTokens']:,} 토큰")
            >>> print(f"남은 토큰: {usage['remainingTokens']:,}")
        """
        response = self._session.get(
            f"{self.base_url}/api/v1/usage",
            timeout=self.timeout
        )

        if not response.ok:
            self._handle_error(response)

        return response.json().get("usage", {})

    def __repr__(self):
        return f"AIClient(api_key='{self.api_key[:20]}...', base_url='{self.base_url}')"


# 편의를 위한 모듈 레벨 함수
_default_client: Optional[AIClient] = None

def configure(api_key: str, encryption_key: str, **kwargs):
    """
    기본 클라이언트 설정

    Example:
        >>> import pns_ai
        >>> pns_ai.configure(api_key="pns_sk_live_xxx", encryption_key="xxx")
        >>> response = pns_ai.chat("안녕")
    """
    global _default_client
    _default_client = AIClient(api_key, encryption_key, **kwargs)

def chat(message: str, **kwargs) -> ChatResponse:
    """기본 클라이언트로 채팅"""
    if not _default_client:
        raise RuntimeError("먼저 pns_ai.configure()를 호출하세요")
    return _default_client.chat(message, **kwargs)

def chat_stream(message: str, **kwargs) -> Iterator[str]:
    """기본 클라이언트로 스트리밍 채팅"""
    if not _default_client:
        raise RuntimeError("먼저 pns_ai.configure()를 호출하세요")
    return _default_client.chat_stream(message, **kwargs)


if __name__ == "__main__":
    # 테스트/예제
    print(f"PNS AI SDK v{__version__}")
    print("사용법: from pns_ai import AIClient")
