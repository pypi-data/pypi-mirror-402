"""
Karrot Chat Library - Exceptions
당근마켓 채팅 관련 예외 클래스 정의
"""

from typing import Optional

from .enums import Status


class KarrotException(Exception):
    """당근마켓 라이브러리 기본 예외"""

    def __init__(self, message: str = "An error occurred"):
        self.message = message
        super().__init__(self.message)


class AuthenticationError(KarrotException):
    """인증 관련 오류"""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message)


class TokenExpiredError(AuthenticationError):
    """토큰 만료 오류"""

    def __init__(self, message: str = "Token has expired"):
        super().__init__(message)


class InvalidTokenError(AuthenticationError):
    """유효하지 않은 토큰 오류"""

    def __init__(self, message: str = "Invalid token"):
        super().__init__(message)


class ConnectionError(KarrotException):
    """연결 관련 오류"""

    def __init__(self, message: str = "Connection failed"):
        super().__init__(message)


class WebSocketError(ConnectionError):
    """WebSocket 관련 오류"""

    def __init__(self, message: str = "WebSocket error", code: Optional[int] = None, reason: Optional[str] = None):
        self.code = code
        self.reason = reason
        super().__init__(message)


class DisconnectedError(ConnectionError):
    """연결 끊김 오류"""

    def __init__(self, message: str = "Disconnected from server"):
        super().__init__(message)


class APIError(KarrotException):
    """API 관련 오류"""

    def __init__(self, message: str = "API error", status: Status = Status.UNKNOWN, status_message: Optional[str] = None):
        self.status = status
        self.status_message = status_message
        full_message = f"{message}: {status.name}"
        if status_message:
            full_message += f" - {status_message}"
        super().__init__(full_message)


class NotFoundError(APIError):
    """리소스를 찾을 수 없음"""

    def __init__(self, message: str = "Resource not found", status_message: Optional[str] = None):
        super().__init__(message, Status.NOT_FOUND, status_message)


class InvalidRequestError(APIError):
    """잘못된 요청"""

    def __init__(self, message: str = "Invalid request", status_message: Optional[str] = None):
        super().__init__(message, Status.INVALID_REQUEST, status_message)


class PermissionDeniedError(APIError):
    """권한 없음"""

    def __init__(self, message: str = "Permission denied", status_message: Optional[str] = None):
        super().__init__(message, Status.PERMISSION_DENIED, status_message)


class BlockedUserError(APIError):
    """차단된 사용자"""

    def __init__(self, message: str = "User is blocked", is_blocked_by_me: bool = False):
        self.is_blocked_by_me = is_blocked_by_me
        status = Status.BLOCKED_USER if is_blocked_by_me else Status.USER_BLOCKED
        if is_blocked_by_me:
            status_message = "차단한 사용자에게는 메시지를 보낼 수 없어요."
        else:
            status_message = "대화 상대에게 차단되어 메시지를 보낼 수 없어요."
        super().__init__(message, status, status_message)


class MessageError(KarrotException):
    """메시지 관련 오류"""

    def __init__(self, message: str = "Message error"):
        super().__init__(message)


class SendMessageError(MessageError):
    """메시지 전송 오류"""

    def __init__(self, message: str = "Failed to send message"):
        super().__init__(message)


class ChannelError(KarrotException):
    """채널 관련 오류"""

    def __init__(self, message: str = "Channel error"):
        super().__init__(message)


class ChannelNotFoundError(ChannelError):
    """채널을 찾을 수 없음"""

    def __init__(self, channel_id: str = ""):
        self.channel_id = channel_id
        super().__init__(f"Channel not found: {channel_id}")


class ProtocolError(KarrotException):
    """프로토콜 관련 오류"""

    def __init__(self, message: str = "Protocol error"):
        super().__init__(message)


class SerializationError(ProtocolError):
    """직렬화 오류"""

    def __init__(self, message: str = "Serialization failed"):
        super().__init__(message)


class DeserializationError(ProtocolError):
    """역직렬화 오류"""

    def __init__(self, message: str = "Deserialization failed"):
        super().__init__(message)


class TimeoutError(KarrotException):
    """타임아웃 오류"""

    def __init__(self, message: str = "Request timed out"):
        super().__init__(message)


class RateLimitError(KarrotException):
    """속도 제한 오류"""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[float] = None):
        self.retry_after = retry_after
        super().__init__(message)


def raise_for_status(status: int, status_message: Optional[str] = None) -> None:
    """상태 코드에 따라 적절한 예외 발생"""
    if status == Status.SUCCESS:
        return

    error_map = {
        Status.NOT_FOUND: NotFoundError,
        Status.INVALID_REQUEST: InvalidRequestError,
        Status.PERMISSION_DENIED: PermissionDeniedError,
        Status.USER_BLOCKED: lambda msg: BlockedUserError(msg, is_blocked_by_me=False),
        Status.BLOCKED_USER: lambda msg: BlockedUserError(msg, is_blocked_by_me=True),
        Status.TIMEOUT: TimeoutError,
        Status.UNAUTHENTICATED: AuthenticationError,
    }

    if status in error_map:
        error_class = error_map[status]
        if callable(error_class) and not isinstance(error_class, type):
            raise error_class(status_message or "Error")
        elif isinstance(error_class, type) and issubclass(error_class, APIError):
            raise error_class(status_message=status_message)
        else:
            raise error_class(status_message or "Error")
    else:
        raise APIError(f"Unknown error (status={status})", Status(status) if status in Status._value2member_map_ else Status.UNKNOWN, status_message)
