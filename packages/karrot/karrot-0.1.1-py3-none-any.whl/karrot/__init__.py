"""
Karrot Chat Library
당근마켓 채팅 Python 라이브러리

discord.py 스타일의 이벤트 기반 채팅 클라이언트입니다.

Example:
    ```python
    from karrot import Client, Message

    client = Client(command_prefix="!")

    @client.event
    async def on_ready():
        print(f"로그인: {client.user.nickname}")

    @client.event
    async def on_message(message: Message):
        print(f"[{message.sender_nickname}] {message.text}")

    @client.command("도움말", aliases=["help"])
    async def help_command(message: Message, args: str):
        await message.reply("도움말입니다.")

    client.run("your_token")
    ```
"""

__title__ = 'karrot'
__author__ = 'deongdion'
__license__ = 'MIT'
__version__ = '0.1.1'

from .client import Client, Command
from .models import (
    User,
    Message,
    Channel,
    Member,
    BizAccount,
    Sticker,
    Image,
    Timestamp,
    PagingKey,
    UnreadCount,
    ReadEvent,
    MemberEvent,
)
from .enums import (
    Status,
    MessageType,
    ChannelType,
    UserType,
    Range,
    PagingKind,
    FilterID,
    SocketState,
    AuthType,
    EventType,
)
from .exceptions import (
    KarrotException,
    AuthenticationError,
    TokenExpiredError,
    InvalidTokenError,
    ConnectionError,
    WebSocketError,
    DisconnectedError,
    APIError,
    NotFoundError,
    InvalidRequestError,
    PermissionDeniedError,
    BlockedUserError,
    MessageError,
    SendMessageError,
    ChannelError,
    ChannelNotFoundError,
    ProtocolError,
    SerializationError,
    DeserializationError,
    TimeoutError,
    RateLimitError,
)

__all__ = [
    # Client
    'Client',
    'Command',

    # Models
    'User',
    'Message',
    'Channel',
    'Member',
    'BizAccount',
    'Sticker',
    'Image',
    'Timestamp',
    'PagingKey',
    'UnreadCount',
    'ReadEvent',
    'MemberEvent',

    # Enums
    'Status',
    'MessageType',
    'ChannelType',
    'UserType',
    'Range',
    'PagingKind',
    'FilterID',
    'SocketState',
    'AuthType',
    'EventType',

    # Exceptions
    'KarrotException',
    'AuthenticationError',
    'TokenExpiredError',
    'InvalidTokenError',
    'ConnectionError',
    'WebSocketError',
    'DisconnectedError',
    'APIError',
    'NotFoundError',
    'InvalidRequestError',
    'PermissionDeniedError',
    'BlockedUserError',
    'MessageError',
    'SendMessageError',
    'ChannelError',
    'ChannelNotFoundError',
    'ProtocolError',
    'SerializationError',
    'DeserializationError',
    'TimeoutError',
    'RateLimitError',
]
