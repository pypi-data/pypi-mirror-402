"""
Karrot Chat Library - WebSocket Gateway
당근마켓 채팅 WebSocket 연결 관리
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional, Callable, Dict, Any, TYPE_CHECKING
from urllib.parse import urlencode

import websockets
from websockets.client import WebSocketClientProtocol

from .enums import SocketState, AuthType
from .protocol import MessageBuilder, ResponseParser
from .exceptions import (
    WebSocketError, DisconnectedError, AuthenticationError
)

if TYPE_CHECKING:
    from .client import Client

logger = logging.getLogger('karrot.gateway')


class KarrotGateway:
    """당근마켓 채팅 WebSocket 게이트웨이"""

    # WebSocket 엔드포인트
    WS_URL_TEMPLATE = "wss://rocket-chat-pub.{region}.karrotmarket.com/ws"
    DEFAULT_REGION = "kr"

    # 재연결 설정
    INITIAL_RECONNECT_DELAY = 1.0
    MAX_RECONNECT_DELAY = 10.0
    RECONNECT_DELAY_MULTIPLIER = 2.0

    def __init__(self, client: 'Client'):
        self.client = client
        self._ws: Optional[WebSocketClientProtocol] = None
        self._state = SocketState.CLOSED
        self._reconnect_delay = self.INITIAL_RECONNECT_DELAY
        self._should_reconnect = True
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._receive_task: Optional[asyncio.Task] = None
        self._message_handlers: Dict[str, Callable] = {}

    @property
    def state(self) -> SocketState:
        """현재 연결 상태"""
        return self._state

    @property
    def is_connected(self) -> bool:
        """연결 여부"""
        return self._state == SocketState.OPEN

    def _build_ws_url(self) -> str:
        """WebSocket URL 생성"""
        base_url = self.WS_URL_TEMPLATE.format(region=self.client.region or self.DEFAULT_REGION)

        # 인증 파라미터 구성
        params = {}
        if self.client._auth_type == AuthType.ACCESS_TOKEN:
            params['access_token_v2'] = self.client.token
            params['x-rocketchat-web-client-version'] = '99.99.99'
        elif self.client._auth_type == AuthType.BIZ_TOKEN:
            params['x_business_web_login_token'] = self.client.token
        elif self.client._auth_type == AuthType.QR_TOKEN:
            params['access_token'] = self.client.token

        return f"{base_url}?{urlencode(params)}"

    async def connect(self) -> None:
        """WebSocket 연결"""
        if self._state == SocketState.OPEN:
            logger.warning("Already connected")
            return

        self._state = SocketState.CONNECTING
        self._should_reconnect = True

        try:
            url = self._build_ws_url()
            logger.info(f"Connecting to WebSocket...")

            self._ws = await websockets.connect(
                url,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=5
            )

            self._state = SocketState.OPEN
            self._reconnect_delay = self.INITIAL_RECONNECT_DELAY
            logger.info("WebSocket connected")

            # 초기 요청 전송
            await self._send_initial_requests()

            # 메시지 수신 태스크 시작
            self._receive_task = asyncio.create_task(self._receive_loop())

            # 연결 이벤트 발생
            await self.client._dispatch('connect')

        except Exception as e:
            self._state = SocketState.CLOSED
            logger.error(f"Connection failed: {e}")
            raise WebSocketError(f"Connection failed: {e}")

    async def disconnect(self) -> None:
        """WebSocket 연결 해제"""
        self._should_reconnect = False
        self._state = SocketState.CLOSING

        # 태스크 취소
        if self._receive_task and not self._receive_task.done():
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass

        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

        # WebSocket 닫기
        if self._ws:
            await self._ws.close()
            self._ws = None

        self._state = SocketState.CLOSED
        logger.info("WebSocket disconnected")

        # 연결 해제 이벤트 발생
        await self.client._dispatch('disconnect')

    async def _send_initial_requests(self) -> None:
        """초기 요청 전송 (스티커, 비즈니스 계정 등)"""
        # GetStickersRequest
        stickers_inner = MessageBuilder.build_get_stickers_request()
        stickers_request = MessageBuilder.build_request(
            name="GetStickersRequest",
            user_id=self.client.user_id,
            inner_message=stickers_inner,
            field_number=MessageBuilder.FIELD_GET_STICKERS
        )
        await self.send(stickers_request)

        # GetBizAccountsRequest
        biz_inner = MessageBuilder.build_get_biz_accounts_request()
        biz_request = MessageBuilder.build_request(
            name="GetBizAccountsRequest",
            user_id=self.client.user_id,
            inner_message=biz_inner,
            field_number=MessageBuilder.FIELD_GET_BIZ_ACCOUNTS
        )
        await self.send(biz_request)

    async def send(self, data: bytes) -> None:
        """데이터 전송"""
        if not self._ws or self._state != SocketState.OPEN:
            raise DisconnectedError("Not connected to WebSocket")

        try:
            await self._ws.send(data)
        except Exception as e:
            logger.error(f"Send failed: {e}")
            raise WebSocketError(f"Send failed: {e}")

    async def _receive_loop(self) -> None:
        """메시지 수신 루프"""
        try:
            while self._state == SocketState.OPEN and self._ws:
                try:
                    data = await self._ws.recv()

                    if isinstance(data, bytes):
                        await self._handle_message(data)
                    else:
                        logger.warning(f"Received non-binary data: {type(data)}")

                except websockets.ConnectionClosed as e:
                    logger.warning(f"Connection closed: code={e.code}, reason={e.reason}")

                    # 인증 실패 처리
                    if e.code == 1002 and e.reason == "unauthorized":
                        logger.error("Authentication failed - unauthorized")
                        self._should_reconnect = False
                        await self.client._dispatch('error', AuthenticationError("Unauthorized"))
                        break

                    # 재연결 시도
                    if self._should_reconnect:
                        await self._reconnect()
                    break

        except asyncio.CancelledError:
            logger.info("Receive loop cancelled")
        except Exception as e:
            logger.error(f"Receive loop error: {e}")
            await self.client._dispatch('error', e)

    async def _handle_message(self, data: bytes) -> None:
        """수신된 메시지 처리"""
        try:
            response = ResponseParser.parse_response(data)
            name = response.get('name', '')
            status = response.get('status', 0)
            status_message = response.get('statusMessage', '')

            logger.debug(f"Received: {name}, status={status}")

            # 상태 체크
            if status != 0 and status != 1:
                logger.warning(f"Response error: {name}, status={status}, message={status_message}")

            # 이벤트 타입별 처리
            await self._dispatch_response(name, response)

        except Exception as e:
            logger.error(f"Message handling error: {e}")

    async def _dispatch_response(self, name: str, response: Dict[str, Any]) -> None:
        """응답 타입별 이벤트 디스패치"""
        if name == "GetChannelsResponse":
            channels_data = response.get('getChannels', {})
            await self.client._handle_channels_response(channels_data)

        elif name == "GetMessagesResponse":
            messages_data = response.get('getMessages', {})
            await self.client._handle_messages_response(messages_data)

        elif name == "SendMessageResponse":
            message_data = response.get('sendMessage', {})
            await self.client._handle_send_message_response(message_data)

        elif name == "GetChannelResponse":
            channel_data = response.get('getChannel', {})
            await self.client._handle_channel_response(channel_data)

        elif name == "NewMessageEvent":
            message_data = response.get('newMessage', {})
            await self.client._handle_new_message_event(message_data)

        elif name == "ReadMessageEvent":
            read_data = response.get('readMessage', {})
            await self.client._handle_read_event(read_data)

        elif name == "JoinMemberEvent":
            member_data = response.get('joinMember', {})
            await self.client._handle_join_event(member_data)

        elif name == "LeaveMemberEvent":
            member_data = response.get('leaveMember', {})
            await self.client._handle_leave_event(member_data)

        elif name == "MarkAsReadResponse":
            read_data = response.get('markAsRead', {})
            await self.client._handle_mark_as_read_response(read_data)

        elif name == "GetStickersResponse":
            stickers_data = response.get('getStickers', {})
            await self.client._handle_stickers_response(stickers_data)

        elif name == "GetBizAccountsResponse":
            biz_data = response.get('getBizAccounts', {})
            await self.client._handle_biz_accounts_response(biz_data)

        elif name == "UpdateMessageEvent":
            message_data = response.get('updateMessage', {})
            await self.client._handle_update_message_event(message_data)

        elif name == "DeleteMessageResponse":
            message_data = response.get('deleteMessage', {})
            await self.client._handle_delete_message_response(message_data)

        elif name == "RenewChannelEvent":
            channel_data = response.get('renewChannel', {})
            await self.client._handle_renew_channel_event(channel_data)

    async def _reconnect(self) -> None:
        """재연결 시도"""
        if not self._should_reconnect:
            return

        self._state = SocketState.CLOSED

        while self._should_reconnect:
            logger.info(f"Reconnecting in {self._reconnect_delay}s...")
            await asyncio.sleep(self._reconnect_delay)

            try:
                await self.connect()
                await self.client._dispatch('reconnect')
                return
            except Exception as e:
                logger.error(f"Reconnection failed: {e}")
                self._reconnect_delay = min(
                    self._reconnect_delay * self.RECONNECT_DELAY_MULTIPLIER,
                    self.MAX_RECONNECT_DELAY
                )
