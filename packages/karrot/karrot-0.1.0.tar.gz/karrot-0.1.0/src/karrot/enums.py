"""
Karrot Chat Library - Enums
당근마켓 채팅 관련 열거형 정의
"""

from enum import IntEnum, auto


class Status(IntEnum):
    """응답 상태 코드"""
    UNKNOWN = 0
    SUCCESS = 1
    INTERNAL_ERROR = 2
    TIMEOUT = 3
    NOT_FOUND = 4
    INVALID_REQUEST = 5
    PERMISSION_DENIED = 6
    ALREADY_EXISTS = 7
    RESOURCE_EXHAUSTED = 8
    FAILED_PRECONDITION = 9
    ABORTED = 10
    OUT_OF_RANGE = 11
    USER_BLOCKED = 12      # 대화 상대에게 차단됨
    BLOCKED_USER = 13      # 내가 차단한 사용자
    UNAUTHENTICATED = 14
    BLOCKED_STATUS = 15    # 차단 상태


class MessageType(IntEnum):
    """메시지 타입"""
    UNKNOWN = 0
    TEXT = 1               # 텍스트 메시지
    IMAGE = 2              # 이미지 (IMAG)
    STICKER = 3            # 스티커 (STIC)
    GALLERY = 4            # 갤러리 (GALL)
    SYSTEM = 5             # 시스템 메시지
    DELETED = 6            # 삭제된 메시지
    TEMPLATE = 7           # 템플릿 메시지
    VOICE = 8              # 음성 메시지
    VIDEO = 9              # 동영상 메시지
    FILE = 10              # 파일 메시지
    LOCATION = 11          # 위치 메시지
    PROMISE = 12           # 약속 메시지


class ChannelType(IntEnum):
    """채널 타입"""
    UNKNOWN = 0
    DIRECT = 1             # 1:1 채팅
    GROUP = 2              # 그룹 채팅
    BUSINESS = 3           # 비즈니스 채팅


class UserType(IntEnum):
    """사용자 타입"""
    UNKNOWN = 0
    NORMAL = 1             # 일반 사용자
    BUSINESS = 2           # 비즈니스 계정
    SYSTEM = 3             # 시스템


class Range(IntEnum):
    """메시지 조회 범위"""
    UNKNOWN = 0
    LESS = 1               # 미만
    LESS_EQUAL = 2         # 이하
    GREATER = 3            # 초과
    GREATER_EQUAL = 4      # 이상


class PagingKind(IntEnum):
    """페이징 종류"""
    UNKNOWN = 0
    FIRST = 1              # 처음부터
    NEXT = 2               # 다음 페이지


class FilterID(IntEnum):
    """필터 ID"""
    NONE = 0
    UNREAD_COUNT = 1       # 읽지 않은 메시지만


class SocketState(IntEnum):
    """WebSocket 연결 상태"""
    CONNECTING = 0
    OPEN = 1
    CLOSING = 2
    CLOSED = 3


class AuthType(IntEnum):
    """인증 타입"""
    QR_TOKEN = 1           # QR 코드 로그인
    BIZ_TOKEN = 2          # 비즈니스 토큰
    ACCESS_TOKEN = 3       # OIDC 액세스 토큰


class EventType(IntEnum):
    """이벤트 타입"""
    # Connection Events
    CONNECT = auto()
    DISCONNECT = auto()
    RECONNECT = auto()

    # Message Events
    MESSAGE = auto()
    MESSAGE_DELETE = auto()
    MESSAGE_UPDATE = auto()

    # Channel Events
    CHANNEL_JOIN = auto()
    CHANNEL_LEAVE = auto()
    CHANNEL_UPDATE = auto()

    # Member Events
    MEMBER_JOIN = auto()
    MEMBER_LEAVE = auto()

    # Read Events
    MESSAGE_READ = auto()

    # Error Events
    ERROR = auto()
