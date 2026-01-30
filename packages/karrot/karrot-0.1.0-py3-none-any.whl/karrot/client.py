"""
Karrot Chat Library - Client
당근마켓 채팅 클라이언트 (discord.py 스타일)
"""

from __future__ import annotations

import asyncio
import logging
import jwt
import inspect
from typing import Optional, List, Dict, Any, Callable, Coroutine, TypeVar, Union
from dataclasses import dataclass, field

from .enums import AuthType, SocketState, MessageType
from .models import User, Message, Channel, Sticker, BizAccount, ReadEvent, MemberEvent, PagingKey
from .protocol import MessageBuilder
from .gateway import KarrotGateway
from .exceptions import (
    KarrotException, InvalidTokenError, DisconnectedError,
    raise_for_status
)

logger = logging.getLogger('karrot')

T = TypeVar('T')
Coro = Coroutine[Any, Any, T]
EventCallback = Callable[..., Coro[None]]
CommandCallback = Callable[..., Coro[None]]


@dataclass
class Command:
    """명령어 정보"""
    name: str
    callback: CommandCallback
    aliases: List[str] = field(default_factory=list)
    description: str = ""

    async def invoke(self, message: Message, args: str) -> None:
        """명령어 실행"""
        await self.callback(message, args)


class Client:
    """
    당근마켓 채팅 클라이언트

    discord.py 스타일의 이벤트 기반 채팅 클라이언트입니다.

    Example:
        ```python
        client = Client(command_prefix="!")

        @client.event
        async def on_ready():
            print(f"로그인: {client.user.nickname}")

        @client.event
        async def on_message(message: Message):
            print(f"[{message.sender_nickname}] {message.text}")

        @client.command("도움말", aliases=["help", "?"])
        async def help_command(message: Message, args: str):
            await message.reply("도움말 메시지입니다.")

        @client.command("핑")
        async def ping_command(message: Message, args: str):
            await message.reply("퐁!")

        client.run("your_token")
        ```
    """

    def __init__(
        self,
        command_prefix: str = "!",
        token: Optional[str] = None,
        region: str = "kr",
        auto_reconnect: bool = True,
        **kwargs
    ):
        """
        클라이언트 초기화

        Args:
            command_prefix: 명령어 접두사 (기본값: "!")
            token: 인증 토큰 (JWT) - run()에서도 전달 가능
            region: 서비스 지역 (기본값: "kr")
            auto_reconnect: 자동 재연결 여부
        """
        self.command_prefix = command_prefix
        self.token: Optional[str] = token
        self.region = region
        self.auto_reconnect = auto_reconnect

        # 사용자 정보 (토큰 디코딩 후 설정)
        self.user_id: int = 0
        self._user_nickname: str = ""
        self._device_id: str = ""
        self._token_exp: int = 0
        self._token_iat: int = 0
        self._token_iss: str = ""
        self._auth_type: AuthType = AuthType.ACCESS_TOKEN

        # 토큰이 있으면 디코딩
        if self.token:
            self._decode_token()

        # 내부 상태
        self._gateway: Optional[KarrotGateway] = None
        self._event_handlers: Dict[str, List[EventCallback]] = {}
        self._commands: Dict[str, Command] = {}
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._closed = False

        # 캐시
        self._channels: Dict[str, Channel] = {}
        self._users: Dict[int, User] = {}
        self._stickers: List[Sticker] = []
        self._biz_accounts: List[BizAccount] = []
        self._me: Optional[User] = None

        # 응답 대기용
        self._pending_responses: Dict[str, asyncio.Future] = {}
        self._response_counter = 0

        # 채널 자동 갱신
        self._channel_refresh_task: Optional[asyncio.Task] = None
        self._channel_refresh_interval: int = kwargs.get('channel_refresh_interval', 10)

    def _decode_token(self) -> None:
        """토큰 디코딩"""
        try:
            payload = jwt.decode(self.token, options={'verify_signature': False})
            self.user_id: int = payload.get('uid', 0)
            self._user_nickname: str = payload.get('unk', '')
            self._device_id: str = payload.get('did', '')
            self._token_exp: int = payload.get('exp', 0)
            self._token_iat: int = payload.get('iat', 0)
            self._token_iss: str = payload.get('iss', '')

            # 인증 타입 결정
            if 'access_token' in self.token.lower() or self._token_iss == 'karrotauth':
                self._auth_type = AuthType.QR_TOKEN
            elif 'biz' in str(payload):
                self._auth_type = AuthType.BIZ_TOKEN
            else:
                self._auth_type = AuthType.ACCESS_TOKEN

            logger.info(f"Token decoded: user_id={self.user_id}, nickname={self._user_nickname}")

        except jwt.DecodeError as e:
            raise InvalidTokenError(f"Invalid token format: {e}")

    @property
    def user(self) -> Optional[User]:
        """현재 로그인한 사용자"""
        if self._me is None:
            self._me = User(
                id=self.user_id,
                nickname=self._user_nickname
            )
        return self._me

    @property
    def channels(self) -> List[Channel]:
        """채널 목록"""
        return list(self._channels.values())

    @property
    def is_connected(self) -> bool:
        """연결 여부"""
        return self._gateway is not None and self._gateway.is_connected

    @property
    def is_closed(self) -> bool:
        """종료 여부"""
        return self._closed

    # ==================== 이벤트 시스템 ====================

    def event(self, coro: EventCallback) -> EventCallback:
        """
        이벤트 핸들러 데코레이터

        Example:
            ```python
            @client.event
            async def on_message(message: Message):
                print(f"Received: {message.content}")
            ```
        """
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError('Event handler must be a coroutine function')

        # 이벤트 이름 추출 (on_message -> message)
        name = coro.__name__
        if name.startswith('on_'):
            name = name[3:]

        if name not in self._event_handlers:
            self._event_handlers[name] = []
        self._event_handlers[name].append(coro)

        return coro

    def add_listener(self, event: str, callback: EventCallback) -> None:
        """이벤트 리스너 추가"""
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(callback)

    def remove_listener(self, event: str, callback: EventCallback) -> None:
        """이벤트 리스너 제거"""
        if event in self._event_handlers:
            try:
                self._event_handlers[event].remove(callback)
            except ValueError:
                pass

    async def _dispatch(self, event: str, *args, **kwargs) -> None:
        """이벤트 디스패치"""
        handlers = self._event_handlers.get(event, [])
        for handler in handlers:
            try:
                await handler(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in event handler {handler.__name__}: {e}")
                # on_error 이벤트 발생
                error_handlers = self._event_handlers.get('error', [])
                for error_handler in error_handlers:
                    try:
                        await error_handler(e)
                    except Exception:
                        pass

    # ==================== 명령어 시스템 ====================

    def command(
        self,
        name: str,
        aliases: Optional[List[str]] = None,
        description: str = ""
    ) -> Callable[[CommandCallback], CommandCallback]:
        """
        명령어 핸들러 데코레이터

        Args:
            name: 명령어 이름 (접두사 제외)
            aliases: 별칭 목록
            description: 명령어 설명

        Example:
            ```python
            @client.command("도움말", aliases=["help", "?"])
            async def help_command(message: Message, args: str):
                await message.reply("도움말입니다.")

            @client.command("핑")
            async def ping(message: Message, args: str):
                await message.reply("퐁!")
            ```
        """
        def decorator(coro: CommandCallback) -> CommandCallback:
            if not asyncio.iscoroutinefunction(coro):
                raise TypeError('Command handler must be a coroutine function')

            cmd = Command(
                name=name,
                callback=coro,
                aliases=aliases or [],
                description=description or coro.__doc__ or ""
            )

            # 명령어 등록
            self._commands[name.lower()] = cmd

            # 별칭도 등록
            for alias in cmd.aliases:
                self._commands[alias.lower()] = cmd

            return coro

        return decorator

    def get_command(self, name: str) -> Optional[Command]:
        """명령어 조회"""
        return self._commands.get(name.lower())

    @property
    def commands(self) -> List[Command]:
        """등록된 명령어 목록 (중복 제거)"""
        seen = set()
        result = []
        for cmd in self._commands.values():
            if cmd.name not in seen:
                seen.add(cmd.name)
                result.append(cmd)
        return result

    async def process_commands(self, message: Message) -> bool:
        """
        메시지에서 명령어 처리

        Args:
            message: 메시지 객체

        Returns:
            명령어가 처리되었으면 True
        """
        text = message.text.strip()

        # 접두사 확인
        if not text.startswith(self.command_prefix):
            return False

        # 명령어 파싱
        content = text[len(self.command_prefix):].strip()
        if not content:
            return False

        parts = content.split(maxsplit=1)
        cmd_name = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        # 명령어 찾기
        cmd = self.get_command(cmd_name)
        if cmd is None:
            # on_command_error 이벤트 발생
            await self._dispatch('command_error', message, cmd_name, f"알 수 없는 명령어: {cmd_name}")
            return False

        # 명령어 실행
        try:
            await cmd.invoke(message, args)
            return True
        except Exception as e:
            logger.error(f"Error in command {cmd_name}: {e}")
            await self._dispatch('command_error', message, cmd_name, str(e))
            return False

    # ==================== 연결 관리 ====================

    async def connect(self) -> None:
        """서버에 연결"""
        if self._gateway is None:
            self._gateway = KarrotGateway(self)

        await self._gateway.connect()

    async def close(self) -> None:
        """연결 종료"""
        self._closed = True

        # 채널 갱신 태스크 취소
        if self._channel_refresh_task and not self._channel_refresh_task.done():
            self._channel_refresh_task.cancel()
            try:
                await self._channel_refresh_task
            except asyncio.CancelledError:
                pass

        if self._gateway:
            await self._gateway.disconnect()

    def run(self, token: Optional[str] = None) -> None:
        """
        클라이언트 실행 (블로킹)

        Args:
            token: 인증 토큰 (JWT) - 생성자에서 전달하지 않은 경우 여기서 전달

        Example:
            ```python
            client = Client(command_prefix="!")
            client.run("your_token")
            ```
        """
        # 토큰 설정
        if token:
            self.token = token
            self._decode_token()
        elif not self.token:
            raise InvalidTokenError("Token is required. Pass it to Client() or run()")

        async def runner():
            try:
                await self.connect()
                # 연결이 끊길 때까지 대기
                while not self._closed:
                    await asyncio.sleep(1)
            finally:
                await self.close()

        try:
            asyncio.run(runner())
        except KeyboardInterrupt:
            logger.info("Interrupted by user")

    async def start(self, token: Optional[str] = None) -> None:
        """
        클라이언트 시작 (비동기)

        Args:
            token: 인증 토큰 (JWT) - 생성자에서 전달하지 않은 경우 여기서 전달

        Example:
            ```python
            async def main():
                client = Client(command_prefix="!")
                await client.start("your_token")
            ```
        """
        # 토큰 설정
        if token:
            self.token = token
            self._decode_token()
        elif not self.token:
            raise InvalidTokenError("Token is required. Pass it to Client() or start()")

        await self.connect()

    # ==================== 채널 관련 ====================

    async def get_channels(self, limit: int = 100, unread_only: bool = False) -> List[Channel]:
        """
        채널 목록 조회

        Args:
            limit: 조회할 채널 수
            unread_only: 읽지 않은 채널만 조회

        Returns:
            채널 목록
        """
        if not self.is_connected:
            raise DisconnectedError("Not connected")

        inner = MessageBuilder.build_get_channels_request(
            limit=limit,
            unread_only=unread_only
        )
        request = MessageBuilder.build_request(
            name="GetChannelsRequest",
            user_id=self.user_id,
            inner_message=inner,
            field_number=MessageBuilder.FIELD_GET_CHANNELS
        )

        await self._gateway.send(request)

        # 응답 대기 (간단한 구현)
        await asyncio.sleep(0.5)
        return list(self._channels.values())

    async def get_channel(self, channel_id: str) -> Optional[Channel]:
        """
        특정 채널 조회

        Args:
            channel_id: 채널 ID

        Returns:
            채널 정보
        """
        if not self.is_connected:
            raise DisconnectedError("Not connected")

        inner = MessageBuilder.build_get_channel_request(channel_id)
        request = MessageBuilder.build_request(
            name="GetChannelRequest",
            user_id=self.user_id,
            inner_message=inner,
            field_number=MessageBuilder.FIELD_GET_CHANNEL
        )

        await self._gateway.send(request)
        await asyncio.sleep(0.3)
        return self._channels.get(channel_id)

    # ==================== 메시지 관련 ====================

    async def get_messages(self, channel_id: str, limit: int = 20,
                           before_message_id: str = "") -> List[Message]:
        """
        메시지 목록 조회

        Args:
            channel_id: 채널 ID
            limit: 조회할 메시지 수
            before_message_id: 이 메시지 이전의 메시지들 조회

        Returns:
            메시지 목록
        """
        if not self.is_connected:
            raise DisconnectedError("Not connected")

        inner = MessageBuilder.build_get_messages_request(
            channel_id=channel_id,
            message_id=before_message_id,
            limit=limit
        )
        request = MessageBuilder.build_request(
            name="GetMessagesRequest",
            user_id=self.user_id,
            inner_message=inner,
            field_number=MessageBuilder.FIELD_GET_MESSAGES
        )

        await self._gateway.send(request)

        # 임시: 응답 캐싱 구현 필요
        await asyncio.sleep(0.5)
        return []

    async def send_message(self, channel_id: str, content: str,
                           receiver_id: int = 0) -> Optional[Message]:
        """
        메시지 전송

        Args:
            channel_id: 채널 ID
            content: 메시지 내용
            receiver_id: 수신자 ID (1:1 채팅에서 필요)

        Returns:
            전송된 메시지
        """
        if not self.is_connected:
            raise DisconnectedError("Not connected")

        # Message 빌드
        message_bytes = MessageBuilder.build_message(
            channel_id=channel_id,
            content=content,
            sender_id=self.user_id,
            receiver_id=receiver_id,
            msg_type="TEXT"
        )

        # SendMessageRequest 빌드
        inner = MessageBuilder.build_send_message_request(message_bytes)
        request = MessageBuilder.build_request(
            name="SendMessageRequest",
            user_id=self.user_id,
            inner_message=inner,
            field_number=MessageBuilder.FIELD_SEND_MESSAGE
        )

        await self._gateway.send(request)
        return None  # 응답에서 메시지 반환 필요

    async def mark_as_read(self, channel_id: str, message_id: str = "") -> bool:
        """
        메시지 읽음 처리

        Args:
            channel_id: 채널 ID
            message_id: 마지막으로 읽은 메시지 ID

        Returns:
            성공 여부
        """
        if not self.is_connected:
            raise DisconnectedError("Not connected")

        inner = MessageBuilder.build_mark_as_read_request(channel_id, message_id)
        request = MessageBuilder.build_request(
            name="MarkAsReadRequest",
            user_id=self.user_id,
            inner_message=inner,
            field_number=MessageBuilder.FIELD_MARK_AS_READ
        )

        await self._gateway.send(request)
        return True

    async def leave_channel(self, channel_id: str) -> bool:
        """
        채널 나가기

        Args:
            channel_id: 채널 ID

        Returns:
            성공 여부
        """
        if not self.is_connected:
            raise DisconnectedError("Not connected")

        inner = MessageBuilder.build_leave_channel_request(channel_id)
        request = MessageBuilder.build_request(
            name="LeaveChannelRequest",
            user_id=self.user_id,
            inner_message=inner,
            field_number=MessageBuilder.FIELD_LEAVE_CHANNEL
        )

        await self._gateway.send(request)
        return True

    # ==================== 내부 이벤트 핸들러 ====================

    async def _handle_channels_response(self, data: Dict[str, Any]) -> None:
        """채널 목록 응답 처리"""
        channels_list = data.get('channelsList', [])
        for channel_data in channels_list:
            channel = Channel.from_dict(channel_data, self)
            if channel:
                self._channels[channel.id] = channel

        logger.debug(f"Received {len(channels_list)} channels")

    async def _handle_messages_response(self, data: Dict[str, Any]) -> None:
        """메시지 목록 응답 처리"""
        messages_list = data.get('messagesList', [])
        messages = [Message.from_dict(m, self) for m in messages_list if m]
        logger.debug(f"Received {len(messages)} messages")

    async def _handle_send_message_response(self, data: Dict[str, Any]) -> None:
        """메시지 전송 응답 처리"""
        message_data = data.get('message')
        if message_data:
            message = Message.from_dict(message_data, self)
            logger.debug(f"Message sent: {message}")

    async def _handle_channel_response(self, data: Dict[str, Any]) -> None:
        """채널 정보 응답 처리"""
        channel_data = data.get('channel')
        if channel_data:
            channel = Channel.from_dict(channel_data, self)
            if channel:
                self._channels[channel.id] = channel
                logger.debug(f"Channel updated: {channel}")

    async def _handle_new_message_event(self, data: Dict[str, Any]) -> None:
        """새 메시지 이벤트 처리"""
        message = Message.from_dict(data, self)
        if message:
            # 채널 참조 설정
            channel = self._channels.get(message.channel_id)
            if channel:
                message._channel = channel

            logger.debug(f"New message: {message}")

            # on_message 이벤트 발생
            await self._dispatch('message', message)

    async def _handle_read_event(self, data: Dict[str, Any]) -> None:
        """읽음 이벤트 처리"""
        read_event = ReadEvent.from_dict(data)
        if read_event:
            await self._dispatch('message_read', read_event)

    async def _handle_join_event(self, data: Dict[str, Any]) -> None:
        """멤버 참여 이벤트 처리"""
        member_event = MemberEvent.from_dict(data, self)
        if member_event and member_event.member:
            # 채널 참조 설정
            channel = self._channels.get(member_event.channel_id)
            if channel:
                member_event._channel = channel
            # 자신이 아닌 경우에만 이벤트 발생
            if member_event.member.id != self.user_id:
                await self._dispatch('member_join', member_event)

    async def _handle_leave_event(self, data: Dict[str, Any]) -> None:
        """멤버 퇴장 이벤트 처리"""
        member_event = MemberEvent.from_dict(data, self)
        if member_event and member_event.member:
            # 채널 참조 설정
            channel = self._channels.get(member_event.channel_id)
            if channel:
                member_event._channel = channel
            if member_event.member.id != self.user_id:
                await self._dispatch('member_leave', member_event)
            else:
                # 자신이 나간 경우
                channel_id = member_event.channel_id
                if channel_id in self._channels:
                    del self._channels[channel_id]

    async def _handle_mark_as_read_response(self, data: Dict[str, Any]) -> None:
        """읽음 처리 응답"""
        logger.debug(f"Mark as read response: {data}")

    async def _handle_stickers_response(self, data: Dict[str, Any]) -> None:
        """스티커 목록 응답 처리"""
        stickers_list = data.get('stickersList', [])
        self._stickers = [Sticker.from_dict(s) for s in stickers_list if s]
        logger.debug(f"Received {len(self._stickers)} stickers")

    async def _handle_biz_accounts_response(self, data: Dict[str, Any]) -> None:
        """비즈니스 계정 목록 응답 처리"""
        biz_list = data.get('bizAccountsList', [])
        self._biz_accounts = [BizAccount.from_dict(b) for b in biz_list if b]
        logger.debug(f"Received {len(self._biz_accounts)} biz accounts")

        # 채널 자동 갱신 태스크 시작
        if self._channel_refresh_task is None or self._channel_refresh_task.done():
            self._channel_refresh_task = asyncio.create_task(self._channel_refresh_loop())

        # ready 이벤트 발생 (초기 데이터 로드 완료)
        await self._dispatch('ready')

    async def _handle_update_message_event(self, data: Dict[str, Any]) -> None:
        """메시지 업데이트 이벤트 처리"""
        message_data = data.get('message')
        if message_data:
            message = Message.from_dict(message_data, self)
            if message:
                await self._dispatch('message_update', message)

    async def _handle_delete_message_response(self, data: Dict[str, Any]) -> None:
        """메시지 삭제 응답 처리"""
        message_data = data.get('message')
        if message_data:
            message = Message.from_dict(message_data, self)
            if message:
                await self._dispatch('message_delete', message)

    async def _handle_renew_channel_event(self, data: Dict[str, Any]) -> None:
        """채널 갱신 이벤트 처리"""
        channel_data = data.get('channel')
        if channel_data:
            channel = Channel.from_dict(channel_data, self)
            if channel:
                self._channels[channel.id] = channel
                logger.debug(f"Channel renewed: {channel}")
                await self._dispatch('channel_update', channel)

    # ==================== 채널 자동 갱신 ====================

    async def _channel_refresh_loop(self) -> None:
        """채널 목록 주기적 갱신 루프"""
        logger.debug(f"Channel refresh loop started (interval: {self._channel_refresh_interval}s)")
        while not self._closed and self.is_connected:
            try:
                await asyncio.sleep(self._channel_refresh_interval)
                if self.is_connected:
                    await self.get_channels(limit=100)
                    logger.debug(f"Channels refreshed: {len(self._channels)} channels")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error refreshing channels: {e}")
        logger.debug("Channel refresh loop stopped")

    def set_channel_refresh_interval(self, seconds: int) -> None:
        """채널 갱신 주기 설정 (초)"""
        self._channel_refresh_interval = max(1, seconds)

    # ==================== 유틸리티 ====================

    def get_channel_by_id(self, channel_id: str) -> Optional[Channel]:
        """ID로 채널 조회 (캐시)"""
        return self._channels.get(channel_id)

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """ID로 사용자 조회 (캐시)"""
        return self._users.get(user_id)

    def __repr__(self) -> str:
        return f"<Client user_id={self.user_id} connected={self.is_connected}>"
