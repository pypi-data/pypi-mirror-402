"""
Karrot Chat Library - Protocol Buffer Handler
당근마켓 채팅 Protocol Buffer 직렬화/역직렬화

main.js 기준 정확한 필드 번호 적용
"""

from __future__ import annotations

import struct
from typing import Dict, Any, Optional, List, Tuple
from io import BytesIO

from .enums import Range, PagingKind, FilterID


# Wire Types
WIRE_VARINT = 0
WIRE_FIXED64 = 1
WIRE_LENGTH_DELIMITED = 2
WIRE_FIXED32 = 5


class ProtobufEncoder:
    """Protocol Buffer 인코더"""

    def __init__(self):
        self.buffer = BytesIO()

    def write_varint(self, value: int) -> None:
        """Varint 인코딩"""
        if value < 0:
            value = value & 0xFFFFFFFFFFFFFFFF  # 음수를 unsigned로 변환

        while value > 0x7F:
            self.buffer.write(bytes([0x80 | (value & 0x7F)]))
            value >>= 7
        self.buffer.write(bytes([value & 0x7F]))

    def write_tag(self, field_number: int, wire_type: int) -> None:
        """필드 태그 작성"""
        self.write_varint((field_number << 3) | wire_type)

    def write_string(self, field_number: int, value: str) -> None:
        """문자열 필드 작성"""
        if not value:
            return
        data = value.encode('utf-8')
        self.write_tag(field_number, WIRE_LENGTH_DELIMITED)
        self.write_varint(len(data))
        self.buffer.write(data)

    def write_bytes(self, field_number: int, value: bytes) -> None:
        """바이트 필드 작성"""
        if not value:
            return
        self.write_tag(field_number, WIRE_LENGTH_DELIMITED)
        self.write_varint(len(value))
        self.buffer.write(value)

    def write_int32(self, field_number: int, value: int) -> None:
        """int32 필드 작성"""
        if value == 0:
            return
        self.write_tag(field_number, WIRE_VARINT)
        self.write_varint(value)

    def write_int64(self, field_number: int, value: int) -> None:
        """int64 필드 작성"""
        if value == 0:
            return
        self.write_tag(field_number, WIRE_VARINT)
        self.write_varint(value)

    def write_bool(self, field_number: int, value: bool) -> None:
        """bool 필드 작성"""
        if not value:
            return
        self.write_tag(field_number, WIRE_VARINT)
        self.write_varint(1 if value else 0)

    def write_enum(self, field_number: int, value: int) -> None:
        """enum 필드 작성"""
        if value == 0:
            return
        self.write_tag(field_number, WIRE_VARINT)
        self.write_varint(value)

    def write_float(self, field_number: int, value: float) -> None:
        """float 필드 작성"""
        if value == 0.0:
            return
        self.write_tag(field_number, WIRE_FIXED32)
        self.buffer.write(struct.pack('<f', value))

    def write_message(self, field_number: int, encoder: 'ProtobufEncoder') -> None:
        """중첩 메시지 필드 작성"""
        data = encoder.get_buffer()
        if not data:
            return
        self.write_tag(field_number, WIRE_LENGTH_DELIMITED)
        self.write_varint(len(data))
        self.buffer.write(data)

    def write_empty_message(self, field_number: int) -> None:
        """빈 메시지 필드 작성"""
        self.write_tag(field_number, WIRE_LENGTH_DELIMITED)
        self.write_varint(0)

    def get_buffer(self) -> bytes:
        """버퍼 반환"""
        return self.buffer.getvalue()


class ProtobufDecoder:
    """Protocol Buffer 디코더"""

    def __init__(self, data: bytes):
        self.buffer = BytesIO(data)
        self.size = len(data)

    def read_varint(self) -> int:
        """Varint 디코딩"""
        result = 0
        shift = 0
        while True:
            byte = self.buffer.read(1)
            if not byte:
                break
            b = byte[0]
            result |= (b & 0x7F) << shift
            if (b & 0x80) == 0:
                break
            shift += 7
        return result

    def read_tag(self) -> Tuple[int, int]:
        """태그 읽기 (field_number, wire_type)"""
        tag = self.read_varint()
        return tag >> 3, tag & 0x7

    def read_string(self) -> str:
        """문자열 읽기"""
        length = self.read_varint()
        data = self.buffer.read(length)
        return data.decode('utf-8', errors='ignore')

    def read_bytes(self) -> bytes:
        """바이트 읽기"""
        length = self.read_varint()
        return self.buffer.read(length)

    def read_int32(self) -> int:
        """int32 읽기"""
        value = self.read_varint()
        if value > 0x7FFFFFFF:
            value -= 0x100000000
        return value

    def read_int64(self) -> int:
        """int64 읽기"""
        value = self.read_varint()
        if value > 0x7FFFFFFFFFFFFFFF:
            value -= 0x10000000000000000
        return value

    def read_bool(self) -> bool:
        """bool 읽기"""
        return self.read_varint() != 0

    def read_float(self) -> float:
        """float 읽기"""
        data = self.buffer.read(4)
        return struct.unpack('<f', data)[0]

    def skip_field(self, wire_type: int) -> None:
        """필드 스킵"""
        if wire_type == WIRE_VARINT:
            self.read_varint()
        elif wire_type == WIRE_FIXED64:
            self.buffer.read(8)
        elif wire_type == WIRE_LENGTH_DELIMITED:
            length = self.read_varint()
            self.buffer.read(length)
        elif wire_type == WIRE_FIXED32:
            self.buffer.read(4)

    def has_more(self) -> bool:
        """더 읽을 데이터가 있는지"""
        return self.buffer.tell() < self.size


class MessageBuilder:
    """
    메시지 빌더 - 당근 채팅 프로토콜에 맞는 메시지 생성

    main.js 기준 정확한 필드 번호:

    Request {
        string name = 1;
        map<string, string> props = 2;
        string id = 3;
        string echo = 4;
        int64 bizAccountId = 5;

        // Request types (100~)
        SendMessageRequest sendMessage = 100;
        GetChannelsRequest getChannels = 101;
        GetMessagesRequest getMessages = 102;
        CreateChannelRequest createChannel = 103;
        MarkAsReadRequest markAsRead = 104;
        LeaveChannelRequest leaveChannel = 105;
        UpdateUserChannelRequest updateUserChannel = 106;
        GetChannelRequest getChannel = 107;
        GetSellerChannelsRequest getSellerChannels = 108;
        GetUnreadCountRequest getUnreadCount = 109;
        CreatePromiseRequest createPromise = 110;
        UpdatePromiseRequest updatePromise = 111;
        DeletePromiseRequest deletePromise = 112;
        GetBizAccountsRequest getBizAccounts = 113;
        GetBizAccountRequest getBizAccount = 114;
        GetStickersRequest getStickers = 115;
        GetSafeNumberRequest getSafeNumber = 116;
        UpdateBlockStatusRequest updateBlockStatus = 117;
        BanUserRequest banUser = 118;
        GetRtcTokenRequest getRtcToken = 119;
        CancelVoiceChannelRequest cancelVoiceChannel = 120;
        RejectVoiceChannelRequest rejectVoiceChannel = 121;
        GetChannelListHeaderRequest getChannelListHeader = 122;
        CloseChannelListHeaderRequest closeChannelListHeader = 123;
        DeleteMessageRequest deleteMessage = 124;
        SendPersistentMenuPostbackRequest sendPersistentMenuPostback = 125;
        GetAutoReplyMetadataRequest getAutoReplyMetadata = 126;
        UpdateAutoReplyMetadataRequest updateAutoReplyMetadata = 127;
        ListAutoRepliesRequest listAutoReplies = 128;
        CreateAutoReplyRequest createAutoReply = 129;
        GetAutoReplyRequest getAutoReply = 130;
        UpdateAutoReplyRequest updateAutoReply = 131;
        DeleteAutoReplyRequest deleteAutoReply = 132;
        CreateAnnouncementRequest createAnnouncement = 133;
        DeleteAnnouncementRequest deleteAnnouncement = 134;
        SetReactionRequest setReaction = 135;
        ListReactionRequest listReaction = 136;
        GetFiltersRequest getFilters = 137;
        GetMemberRequest getMember = 141;
        GetMembersRequest getMembers = 142;
        SearchMembersRequest searchMembers = 143;
        SendButtonPostbackRequest sendButtonPostback = 150;
    }
    """

    # Request field numbers
    FIELD_NAME = 1
    FIELD_PROPS = 2
    FIELD_ID = 3
    FIELD_ECHO = 4
    FIELD_BIZ_ACCOUNT_ID = 5

    # Request type field numbers (main.js 기준)
    FIELD_SEND_MESSAGE = 100
    FIELD_GET_CHANNELS = 101
    FIELD_GET_MESSAGES = 102
    FIELD_CREATE_CHANNEL = 103
    FIELD_MARK_AS_READ = 104
    FIELD_LEAVE_CHANNEL = 105
    FIELD_UPDATE_USER_CHANNEL = 106
    FIELD_GET_CHANNEL = 107
    FIELD_GET_SELLER_CHANNELS = 108
    FIELD_GET_UNREAD_COUNT = 109
    FIELD_CREATE_PROMISE = 110
    FIELD_UPDATE_PROMISE = 111
    FIELD_DELETE_PROMISE = 112
    FIELD_GET_BIZ_ACCOUNTS = 113
    FIELD_GET_BIZ_ACCOUNT = 114
    FIELD_GET_STICKERS = 115
    FIELD_GET_SAFE_NUMBER = 116
    FIELD_UPDATE_BLOCK_STATUS = 117
    FIELD_BAN_USER = 118
    FIELD_GET_RTC_TOKEN = 119
    FIELD_CANCEL_VOICE_CHANNEL = 120
    FIELD_REJECT_VOICE_CHANNEL = 121
    FIELD_GET_CHANNEL_LIST_HEADER = 122
    FIELD_CLOSE_CHANNEL_LIST_HEADER = 123
    FIELD_DELETE_MESSAGE = 124
    FIELD_SEND_PERSISTENT_MENU_POSTBACK = 125
    FIELD_GET_AUTO_REPLY_METADATA = 126
    FIELD_UPDATE_AUTO_REPLY_METADATA = 127
    FIELD_LIST_AUTO_REPLIES = 128
    FIELD_CREATE_AUTO_REPLY = 129
    FIELD_GET_AUTO_REPLY = 130
    FIELD_UPDATE_AUTO_REPLY = 131
    FIELD_DELETE_AUTO_REPLY = 132
    FIELD_CREATE_ANNOUNCEMENT = 133
    FIELD_DELETE_ANNOUNCEMENT = 134
    FIELD_SET_REACTION = 135
    FIELD_LIST_REACTION = 136
    FIELD_GET_FILTERS = 137
    FIELD_GET_MEMBER = 141
    FIELD_GET_MEMBERS = 142
    FIELD_SEARCH_MEMBERS = 143
    FIELD_SEND_BUTTON_POSTBACK = 150

    @staticmethod
    def build_request(name: str, user_id: int, biz_account_id: int = 0,
                      inner_message: Optional[bytes] = None, field_number: int = 0) -> bytes:
        """기본 Request 메시지 빌드"""
        encoder = ProtobufEncoder()

        # name (field 1)
        encoder.write_string(1, name)

        # id (field 3) - user_id를 string으로
        encoder.write_string(3, str(user_id))

        # bizAccountId (field 5) - int64
        if biz_account_id > 0:
            encoder.write_int64(5, biz_account_id)

        # inner message (field_number)
        if field_number > 0:
            if inner_message:
                encoder.write_bytes(field_number, inner_message)
            else:
                # 빈 메시지도 필드는 써야 함
                encoder.write_empty_message(field_number)

        return encoder.get_buffer()

    @staticmethod
    def build_user(user_id: int, user_type: int = 1) -> bytes:
        """
        User 메시지 빌드

        User {
            int64 id = 1;
            string nickname = 2;
            string displayRegionName = 3;
            string profileImage = 4;
            float temperature = 5;
            string messageResponseTime = 6;
            bool isDoNotDisturbOn = 7;
            string doNotDisturbStartTime = 8;
            string doNotDisturbEndTime = 9;
            string badgeImage = 10;
            repeated int32 userFlaggedByMeList = 11;
            string status = 12;
            string targetUri = 13;
            int32 type = 14;
            int32 displayRegionCheckinsCount = 15;
            string doNotDisturbeTimeZone = 16;
            Region region = 17;
            bool isVerified = 18;
            string displayLocationName = 19;
            bool isBizFollower = 20;
            bool isSameCondoMember = 21;
            string subnickname = 22;
            int32 role = 23;
            float mannerTemperature = 101;
            KarrotScore karrotScore = 102;
        }
        """
        encoder = ProtobufEncoder()
        encoder.write_int64(1, user_id)  # id
        encoder.write_int32(14, user_type)  # type
        return encoder.get_buffer()

    @staticmethod
    def build_message(channel_id: str, content: str, sender_id: int, sender_type: int = 1,
                      receiver_id: int = 0, receiver_type: int = 1, msg_type: str = "TEXT") -> bytes:
        """
        Message 메시지 빌드 (main.js 기준)

        Message {
            int64 id = 1;
            string type = 2;           // "TEXT", "IMAG", "STIC", etc.
            string channelId = 3;
            int64 senderId = 4;
            string content = 5;
            Timestamp createTime = 6;
            map<int64, Timestamp> seenMap = 7;
            string data = 8;
            int64 receiverId = 9;
            int64 imageId = 10;
            string imageUrl = 11;
            Link link = 12;
            Promise promise = 13;
            string pictureId = 14;
            SystemMessage systemMessage = 15;
            int32 templateType = 16;
            int32 visible = 17;
            User sender = 18;
            User receiver = 19;
            repeated Image imagesList = 20;
            Timestamp deleteTime = 21;
            MessageContext messageContext = 22;
            repeated ReactionSummary reactionsList = 23;
            ArticleTemplate articleTemplate = 24;
            GenericTemplate genericTemplate = 25;
            LocationTemplate locationTemplate = 26;
            IconTemplate iconTemplate = 27;
            InlineTemplate inlineTemplate = 28;
            BlockTemplate blockTemplate = 29;
            VideoTemplate videoTemplate = 30;
        }
        """
        encoder = ProtobufEncoder()

        # type (field 2)
        encoder.write_string(2, msg_type)

        # channelId (field 3)
        encoder.write_string(3, channel_id)

        # senderId (field 4)
        encoder.write_int64(4, sender_id)

        # content (field 5)
        encoder.write_string(5, content)

        # receiverId (field 9) - 있으면
        if receiver_id > 0:
            encoder.write_int64(9, receiver_id)

        # sender (field 18) - User 메시지
        sender_encoder = ProtobufEncoder()
        sender_encoder.write_int64(1, sender_id)
        sender_encoder.write_int32(14, sender_type)  # type
        encoder.write_message(18, sender_encoder)

        # receiver (field 19) - 있으면
        if receiver_id > 0:
            receiver_encoder = ProtobufEncoder()
            receiver_encoder.write_int64(1, receiver_id)
            receiver_encoder.write_int32(14, receiver_type)
            encoder.write_message(19, receiver_encoder)

        return encoder.get_buffer()

    @staticmethod
    def build_send_message_request(message_bytes: bytes, read_only_channel: bool = False) -> bytes:
        """
        SendMessageRequest 빌드

        SendMessageRequest {
            Message message = 1;
            bool readOnlyChannel = 2;
        }
        """
        encoder = ProtobufEncoder()
        encoder.write_bytes(1, message_bytes)  # message (field 1)
        if read_only_channel:
            encoder.write_bool(2, True)
        return encoder.get_buffer()

    @staticmethod
    def build_get_channels_request(limit: int = 100, paging_key: Optional[Dict] = None,
                                   unread_only: bool = False) -> bytes:
        """
        GetChannelsRequest 빌드

        GetChannelsRequest {
            PagingKey pagingKey = 1;
            bool withLastMessage = 2;
            int32 limit = 3;
            int32 filterId = 4;
        }
        """
        encoder = ProtobufEncoder()

        # pagingKey (field 1)
        if paging_key:
            paging_encoder = ProtobufEncoder()
            paging_encoder.write_int32(1, paging_key.get('kind', PagingKind.NEXT))
            if paging_key.get('time'):
                time_encoder = ProtobufEncoder()
                time_encoder.write_int64(1, paging_key['time'].get('seconds', 0))
                time_encoder.write_int32(2, paging_key['time'].get('nanos', 0))
                paging_encoder.write_message(2, time_encoder)
            encoder.write_message(1, paging_encoder)
        else:
            # 기본 paging key (kind=2)
            paging_encoder = ProtobufEncoder()
            paging_encoder.write_int32(1, PagingKind.NEXT)
            encoder.write_message(1, paging_encoder)

        # withLastMessage (field 2)
        encoder.write_bool(2, True)

        # limit (field 3)
        encoder.write_int32(3, limit)

        # filterId (field 4) - 읽지 않은 메시지만 필터링
        if unread_only:
            encoder.write_int32(4, FilterID.UNREAD_COUNT)

        return encoder.get_buffer()

    @staticmethod
    def build_get_messages_request(channel_id: str, message_id: str = "", limit: int = 20,
                                   range_type: int = Range.LESS_EQUAL) -> bytes:
        """
        GetMessagesRequest 빌드

        GetMessagesRequest {
            string channelId = 1;
            int64 messageId = 2;
            int32 limit = 3;
            Range range = 4;
        }
        """
        encoder = ProtobufEncoder()

        # channelId (field 1)
        encoder.write_string(1, channel_id)

        # messageId (field 2)
        if message_id:
            encoder.write_int64(2, int(message_id))

        # limit (field 3)
        encoder.write_int32(3, limit)

        # range (field 4)
        encoder.write_enum(4, range_type)

        return encoder.get_buffer()

    @staticmethod
    def build_get_channel_request(channel_id: str, with_last_message: bool = True) -> bytes:
        """
        GetChannelRequest 빌드

        GetChannelRequest {
            PagingKey pagingKey = 1;
            string channelId = 2;
            bool withLastMessage = 3;
        }
        """
        encoder = ProtobufEncoder()

        # channelId (field 2)
        encoder.write_string(2, channel_id)

        # withLastMessage (field 3)
        encoder.write_bool(3, with_last_message)

        return encoder.get_buffer()

    @staticmethod
    def build_mark_as_read_request(channel_id: str, message_id: str = "") -> bytes:
        """
        MarkAsReadRequest 빌드

        MarkAsReadRequest {
            string channelId = 1;
            int64 messageId = 2;
        }
        """
        encoder = ProtobufEncoder()

        # channelId (field 1)
        encoder.write_string(1, channel_id)

        # messageId (field 2)
        if message_id:
            encoder.write_int64(2, int(message_id))

        return encoder.get_buffer()

    @staticmethod
    def build_leave_channel_request(channel_id: str) -> bytes:
        """
        LeaveChannelRequest 빌드

        LeaveChannelRequest {
            string channelId = 1;
        }
        """
        encoder = ProtobufEncoder()
        encoder.write_string(1, channel_id)
        return encoder.get_buffer()

    @staticmethod
    def build_delete_message_request(channel_id: str, message_id: str) -> bytes:
        """
        DeleteMessageRequest 빌드

        DeleteMessageRequest {
            string channelId = 1;
            int64 messageId = 2;
        }
        """
        encoder = ProtobufEncoder()
        encoder.write_string(1, channel_id)
        encoder.write_int64(2, int(message_id))
        return encoder.get_buffer()

    @staticmethod
    def build_get_stickers_request() -> bytes:
        """GetStickersRequest 빌드 (빈 메시지)"""
        return b''

    @staticmethod
    def build_get_biz_accounts_request() -> bytes:
        """GetBizAccountsRequest 빌드 (빈 메시지)"""
        return b''

    @staticmethod
    def build_get_unread_count_request() -> bytes:
        """GetUnreadCountRequest 빌드 (빈 메시지)"""
        return b''


class ResponseParser:
    """
    응답 파서 - 당근 채팅 프로토콜 응답 파싱

    main.js 기준 Response 구조:

    Response {
        string name = 1;
        Status status = 2;
        string id = 3;
        string echo = 4;
        int64 bizAccountId = 5;
        string statusMessage = 6;
        StatusAction statusAction = 7;

        // Response types (100~)
        SendMessageResponse sendMessage = 100;
        GetChannelsResponse getChannels = 101;
        GetMessagesResponse getMessages = 102;
        CreateChannelResponse createChannel = 103;
        MarkAsReadResponse markAsRead = 104;
        LeaveChannelResponse leaveChannel = 105;
        UpdateUserChannelResponse updateUserChannel = 106;
        GetChannelResponse getChannel = 107;
        GetSellerChannelsResponse getSellerChannels = 108;
        GetUnreadCountResponse getUnreadCount = 109;
        ...

        // Events (200~)
        NewMessageEvent newMessage = 200;
        ReadMessageEvent readMessage = 201;
        JoinMemberEvent joinMember = 202;
        LeaveMemberEvent leaveMember = 203;
        RenewChannelEvent renewChannel = 204;
        UpdateBubbleGroupEvent updateBubbleGroup = 205;
        UpdateMessageEvent updateMessage = 206;
        JoinVoiceChannelEvent joinVoiceChannel = 211;
        TerminateVoiceChannelEvent terminateVoiceChannel = 212;
    }
    """

    @staticmethod
    def parse_response(data: bytes) -> Dict[str, Any]:
        """Response 메시지 파싱"""
        decoder = ProtobufDecoder(data)
        result = {
            'name': '',
            'status': 0,
            'id': '',
            'echo': '',
            'bizAccountId': 0,
            'statusMessage': ''
        }

        while decoder.has_more():
            field_number, wire_type = decoder.read_tag()

            if field_number == 1 and wire_type == WIRE_LENGTH_DELIMITED:
                result['name'] = decoder.read_string()
            elif field_number == 2 and wire_type == WIRE_VARINT:
                result['status'] = decoder.read_int32()
            elif field_number == 3 and wire_type == WIRE_LENGTH_DELIMITED:
                result['id'] = decoder.read_string()
            elif field_number == 4 and wire_type == WIRE_LENGTH_DELIMITED:
                result['echo'] = decoder.read_string()
            elif field_number == 5 and wire_type == WIRE_VARINT:
                result['bizAccountId'] = decoder.read_int64()
            elif field_number == 6 and wire_type == WIRE_LENGTH_DELIMITED:
                result['statusMessage'] = decoder.read_string()
            elif wire_type == WIRE_LENGTH_DELIMITED:
                # 내부 응답 메시지 (100번대/200번대 필드)
                inner_data = decoder.read_bytes()
                result[f'field_{field_number}'] = inner_data

                # 응답 타입별 파싱
                if field_number == 100:  # SendMessageResponse
                    result['sendMessage'] = ResponseParser._parse_send_message_response(inner_data)
                elif field_number == 101:  # GetChannelsResponse
                    result['getChannels'] = ResponseParser._parse_get_channels_response(inner_data)
                elif field_number == 102:  # GetMessagesResponse
                    result['getMessages'] = ResponseParser._parse_get_messages_response(inner_data)
                elif field_number == 104:  # MarkAsReadResponse
                    result['markAsRead'] = ResponseParser._parse_mark_as_read_response(inner_data)
                elif field_number == 107:  # GetChannelResponse
                    result['getChannel'] = ResponseParser._parse_get_channel_response(inner_data)
                elif field_number == 109:  # GetUnreadCountResponse
                    result['getUnreadCount'] = ResponseParser._parse_get_unread_count_response(inner_data)
                elif field_number == 113:  # GetBizAccountsResponse
                    result['getBizAccounts'] = ResponseParser._parse_get_biz_accounts_response(inner_data)
                elif field_number == 115:  # GetStickersResponse
                    result['getStickers'] = ResponseParser._parse_get_stickers_response(inner_data)
                elif field_number == 124:  # DeleteMessageResponse
                    result['deleteMessage'] = ResponseParser._parse_delete_message_response(inner_data)
                elif field_number == 200:  # NewMessageEvent
                    result['newMessage'] = ResponseParser._parse_new_message_event(inner_data)
                elif field_number == 201:  # ReadMessageEvent
                    result['readMessage'] = ResponseParser._parse_read_event(inner_data)
                elif field_number == 202:  # JoinMemberEvent
                    result['joinMember'] = ResponseParser._parse_member_event(inner_data)
                elif field_number == 203:  # LeaveMemberEvent
                    result['leaveMember'] = ResponseParser._parse_member_event(inner_data)
                elif field_number == 204:  # RenewChannelEvent
                    result['renewChannel'] = ResponseParser._parse_renew_channel_event(inner_data)
                elif field_number == 206:  # UpdateMessageEvent
                    result['updateMessage'] = ResponseParser._parse_update_message_event(inner_data)
            else:
                decoder.skip_field(wire_type)

        return result

    @staticmethod
    def _parse_send_message_response(data: bytes) -> Dict[str, Any]:
        """SendMessageResponse 파싱"""
        decoder = ProtobufDecoder(data)
        result = {}

        while decoder.has_more():
            field_number, wire_type = decoder.read_tag()

            if field_number == 1 and wire_type == WIRE_LENGTH_DELIMITED:
                result['message'] = ResponseParser._parse_message(decoder.read_bytes())
            else:
                decoder.skip_field(wire_type)

        return result

    @staticmethod
    def _parse_get_channels_response(data: bytes) -> Dict[str, Any]:
        """GetChannelsResponse 파싱"""
        decoder = ProtobufDecoder(data)
        result = {
            'channelsList': [],
            'nextPagingKey': None,
            'unreadCount': 0
        }

        while decoder.has_more():
            field_number, wire_type = decoder.read_tag()

            if field_number == 1 and wire_type == WIRE_LENGTH_DELIMITED:
                channel_data = decoder.read_bytes()
                channel = ResponseParser._parse_channel(channel_data)
                result['channelsList'].append(channel)
            elif field_number == 2 and wire_type == WIRE_LENGTH_DELIMITED:
                result['nextPagingKey'] = ResponseParser._parse_paging_key(decoder.read_bytes())
            elif field_number == 3 and wire_type == WIRE_VARINT:
                result['unreadCount'] = decoder.read_int32()
            else:
                decoder.skip_field(wire_type)

        return result

    @staticmethod
    def _parse_get_messages_response(data: bytes) -> Dict[str, Any]:
        """GetMessagesResponse 파싱"""
        decoder = ProtobufDecoder(data)
        result = {
            'messagesList': []
        }

        while decoder.has_more():
            field_number, wire_type = decoder.read_tag()

            if field_number == 1 and wire_type == WIRE_LENGTH_DELIMITED:
                message_data = decoder.read_bytes()
                message = ResponseParser._parse_message(message_data)
                result['messagesList'].append(message)
            else:
                decoder.skip_field(wire_type)

        return result

    @staticmethod
    def _parse_get_channel_response(data: bytes) -> Dict[str, Any]:
        """GetChannelResponse 파싱"""
        decoder = ProtobufDecoder(data)
        result = {}

        while decoder.has_more():
            field_number, wire_type = decoder.read_tag()

            if field_number == 1 and wire_type == WIRE_LENGTH_DELIMITED:
                result['channel'] = ResponseParser._parse_channel(decoder.read_bytes())
            elif field_number == 2 and wire_type == WIRE_LENGTH_DELIMITED:
                result['persistentMenu'] = ResponseParser._parse_persistent_menu(decoder.read_bytes())
            else:
                decoder.skip_field(wire_type)

        return result

    @staticmethod
    def _parse_mark_as_read_response(data: bytes) -> Dict[str, Any]:
        """MarkAsReadResponse 파싱"""
        return {}

    @staticmethod
    def _parse_get_unread_count_response(data: bytes) -> Dict[str, Any]:
        """GetUnreadCountResponse 파싱"""
        decoder = ProtobufDecoder(data)
        result = {'unreadCount': 0}

        while decoder.has_more():
            field_number, wire_type = decoder.read_tag()
            if field_number == 1 and wire_type == WIRE_VARINT:
                result['unreadCount'] = decoder.read_int32()
            else:
                decoder.skip_field(wire_type)

        return result

    @staticmethod
    def _parse_get_biz_accounts_response(data: bytes) -> Dict[str, Any]:
        """GetBizAccountsResponse 파싱"""
        decoder = ProtobufDecoder(data)
        result = {'bizAccountsList': []}

        while decoder.has_more():
            field_number, wire_type = decoder.read_tag()
            if field_number == 1 and wire_type == WIRE_LENGTH_DELIMITED:
                result['bizAccountsList'].append(ResponseParser._parse_biz_account(decoder.read_bytes()))
            else:
                decoder.skip_field(wire_type)

        return result

    @staticmethod
    def _parse_get_stickers_response(data: bytes) -> Dict[str, Any]:
        """GetStickersResponse 파싱"""
        decoder = ProtobufDecoder(data)
        result = {'stickersList': []}

        while decoder.has_more():
            field_number, wire_type = decoder.read_tag()
            if field_number == 1 and wire_type == WIRE_LENGTH_DELIMITED:
                result['stickersList'].append(ResponseParser._parse_sticker(decoder.read_bytes()))
            else:
                decoder.skip_field(wire_type)

        return result

    @staticmethod
    def _parse_delete_message_response(data: bytes) -> Dict[str, Any]:
        """DeleteMessageResponse 파싱"""
        decoder = ProtobufDecoder(data)
        result = {}

        while decoder.has_more():
            field_number, wire_type = decoder.read_tag()
            if field_number == 1 and wire_type == WIRE_LENGTH_DELIMITED:
                result['message'] = ResponseParser._parse_message(decoder.read_bytes())
            else:
                decoder.skip_field(wire_type)

        return result

    @staticmethod
    def _parse_channel(data: bytes) -> Dict[str, Any]:
        """
        Channel 메시지 파싱 (main.js 기준)

        Channel {
            string id = 1;
            string resourceType = 2;
            int64 resourceId = 3;
            string deprecated = 4;
            repeated int64 memberIdsList = 5;
            bool isFavorite = 6;
            bool isReadOnly = 7;
            bool isDisabled = 8;
            bool isMute = 9;
            int32 unreadCount = 10;
            int64 lastSeenId = 11;
            Timestamp lastMessageTime = 12;
            Timestamp createTime = 13;
            Message lastMessage = 14;
            User receiver = 15;
            Article article = 16;
            Promise promise = 17;
            Notice notice = 18;
            bool isPromisable = 20;
            bool isReviewable = 21;
            EnabledFeature enabledFeature = 22;
            User me = 23;
            BizAccount bizAccount = 24;
            string targetUri = 26;
            int32 type = 27;
            repeated User membersList = 28;
            User owner = 29;
            string title = 30;
            string thumbnail = 31;
            WebView webView = 32;
            int32 memberLimit = 33;
            bool closed = 34;
            Input input = 35;
            BubbleGroup bubbleGroup = 36;
            Introduction introduction = 37;
            repeated ToolboxButton toolboxButtonsList = 38;
            bool isTemporary = 39;
            Timestamp favoriteTime = 40;
            int32 unreadMentionsCount = 41;
            int32 memberCount = 42;
            int32 unreadReplyCount = 43;
            int32 commonFilterId = 44;
            int32 serviceFilterId = 45;
            string coverImageText = 49;
            string coverImageUrl = 50;
            string resourceIconUrl = 51;
            int64 lastMessageId = 52;
            int32 badge = 53;
        }
        """
        decoder = ProtobufDecoder(data)
        result = {
            'id': '',
            'resourceType': '',
            'resourceId': 0,
            'memberIdsList': [],
            'isFavorite': False,
            'isReadOnly': False,
            'isDisabled': False,
            'isMuted': False,
            'unreadCount': 0,
            'lastSeenId': 0,
            'lastMessageTime': None,
            'createTime': None,
            'lastMessage': None,
            'receiver': None,
            'me': None,
            'bizAccount': None,
            'targetUri': '',
            'type': 0,
            'membersList': [],
            'owner': None,
            'name': '',  # title -> name
            'imageUrl': '',  # thumbnail -> imageUrl
            'memberLimit': 0,
            'memberCount': 0,
            'closed': False,
            'isTemporary': False,
            'unreadMentionsCount': 0,
            'unreadReplyCount': 0,
            'lastMessageId': 0,
            'badge': 0
        }

        while decoder.has_more():
            field_number, wire_type = decoder.read_tag()

            if field_number == 1 and wire_type == WIRE_LENGTH_DELIMITED:
                result['id'] = decoder.read_string()
            elif field_number == 2 and wire_type == WIRE_LENGTH_DELIMITED:
                result['resourceType'] = decoder.read_string()
            elif field_number == 3 and wire_type == WIRE_VARINT:
                result['resourceId'] = decoder.read_int64()
            elif field_number == 5 and wire_type == WIRE_VARINT:
                result['memberIdsList'].append(decoder.read_int64())
            elif field_number == 6 and wire_type == WIRE_VARINT:
                result['isFavorite'] = decoder.read_bool()
            elif field_number == 7 and wire_type == WIRE_VARINT:
                result['isReadOnly'] = decoder.read_bool()
            elif field_number == 8 and wire_type == WIRE_VARINT:
                result['isDisabled'] = decoder.read_bool()
            elif field_number == 9 and wire_type == WIRE_VARINT:
                result['isMuted'] = decoder.read_bool()
            elif field_number == 10 and wire_type == WIRE_VARINT:
                result['unreadCount'] = decoder.read_int32()
            elif field_number == 11 and wire_type == WIRE_VARINT:
                result['lastSeenId'] = decoder.read_int64()
            elif field_number == 12 and wire_type == WIRE_LENGTH_DELIMITED:
                result['lastMessageTime'] = ResponseParser._parse_timestamp(decoder.read_bytes())
            elif field_number == 13 and wire_type == WIRE_LENGTH_DELIMITED:
                result['createTime'] = ResponseParser._parse_timestamp(decoder.read_bytes())
            elif field_number == 14 and wire_type == WIRE_LENGTH_DELIMITED:
                result['lastMessage'] = ResponseParser._parse_message(decoder.read_bytes())
            elif field_number == 15 and wire_type == WIRE_LENGTH_DELIMITED:
                result['receiver'] = ResponseParser._parse_user(decoder.read_bytes())
            elif field_number == 23 and wire_type == WIRE_LENGTH_DELIMITED:
                result['me'] = ResponseParser._parse_user(decoder.read_bytes())
            elif field_number == 24 and wire_type == WIRE_LENGTH_DELIMITED:
                result['bizAccount'] = ResponseParser._parse_biz_account(decoder.read_bytes())
            elif field_number == 26 and wire_type == WIRE_LENGTH_DELIMITED:
                result['targetUri'] = decoder.read_string()
            elif field_number == 27 and wire_type == WIRE_VARINT:
                result['type'] = decoder.read_int32()
            elif field_number == 28 and wire_type == WIRE_LENGTH_DELIMITED:
                member_data = decoder.read_bytes()
                result['membersList'].append(ResponseParser._parse_user(member_data))
            elif field_number == 29 and wire_type == WIRE_LENGTH_DELIMITED:
                result['owner'] = ResponseParser._parse_user(decoder.read_bytes())
            elif field_number == 30 and wire_type == WIRE_LENGTH_DELIMITED:
                result['name'] = decoder.read_string()  # title -> name
            elif field_number == 31 and wire_type == WIRE_LENGTH_DELIMITED:
                result['imageUrl'] = decoder.read_string()  # thumbnail -> imageUrl
            elif field_number == 33 and wire_type == WIRE_VARINT:
                result['memberLimit'] = decoder.read_int32()
            elif field_number == 34 and wire_type == WIRE_VARINT:
                result['closed'] = decoder.read_bool()
            elif field_number == 39 and wire_type == WIRE_VARINT:
                result['isTemporary'] = decoder.read_bool()
            elif field_number == 41 and wire_type == WIRE_VARINT:
                result['unreadMentionsCount'] = decoder.read_int32()
            elif field_number == 42 and wire_type == WIRE_VARINT:
                result['memberCount'] = decoder.read_int32()
            elif field_number == 43 and wire_type == WIRE_VARINT:
                result['unreadReplyCount'] = decoder.read_int32()
            elif field_number == 52 and wire_type == WIRE_VARINT:
                result['lastMessageId'] = decoder.read_int64()
            elif field_number == 53 and wire_type == WIRE_VARINT:
                result['badge'] = decoder.read_int32()
            else:
                decoder.skip_field(wire_type)

        # memberCount가 없으면 membersList 길이 사용
        if result['memberCount'] == 0 and result['membersList']:
            result['memberCount'] = len(result['membersList'])

        return result

    @staticmethod
    def _parse_message(data: bytes) -> Dict[str, Any]:
        """
        Message 메시지 파싱 (main.js 기준)

        Message {
            int64 id = 1;
            string type = 2;
            string channelId = 3;
            int64 senderId = 4;
            string content = 5;
            Timestamp createTime = 6;
            map<int64, Timestamp> seenMap = 7;
            string data = 8;
            int64 receiverId = 9;
            int64 imageId = 10;
            string imageUrl = 11;
            Link link = 12;
            Promise promise = 13;
            string pictureId = 14;
            SystemMessage systemMessage = 15;
            int32 templateType = 16;
            int32 visible = 17;
            User sender = 18;
            User receiver = 19;
            repeated Image imagesList = 20;
            Timestamp deleteTime = 21;
            MessageContext messageContext = 22;
            repeated ReactionSummary reactionsList = 23;
            ...
        }
        """
        decoder = ProtobufDecoder(data)
        result = {
            'id': '',
            'type': 'TEXT',
            'channelId': '',
            'senderId': 0,
            'content': '',
            'createTime': None,
            'data': '',
            'receiverId': 0,
            'imageId': 0,
            'imageUrl': '',
            'sender': None,
            'receiver': None,
            'imagesList': [],
            'deleteTime': None,
            'senderNickname': '',
            'senderProfile': ''
        }

        while decoder.has_more():
            field_number, wire_type = decoder.read_tag()

            if field_number == 1 and wire_type == WIRE_VARINT:
                result['id'] = str(decoder.read_int64())
            elif field_number == 2 and wire_type == WIRE_LENGTH_DELIMITED:
                result['type'] = decoder.read_string()
            elif field_number == 3 and wire_type == WIRE_LENGTH_DELIMITED:
                result['channelId'] = decoder.read_string()
            elif field_number == 4 and wire_type == WIRE_VARINT:
                result['senderId'] = decoder.read_int64()
            elif field_number == 5 and wire_type == WIRE_LENGTH_DELIMITED:
                result['content'] = decoder.read_string()
            elif field_number == 6 and wire_type == WIRE_LENGTH_DELIMITED:
                result['createTime'] = ResponseParser._parse_timestamp(decoder.read_bytes())
            elif field_number == 8 and wire_type == WIRE_LENGTH_DELIMITED:
                result['data'] = decoder.read_string()
            elif field_number == 9 and wire_type == WIRE_VARINT:
                result['receiverId'] = decoder.read_int64()
            elif field_number == 10 and wire_type == WIRE_VARINT:
                result['imageId'] = decoder.read_int64()
            elif field_number == 11 and wire_type == WIRE_LENGTH_DELIMITED:
                result['imageUrl'] = decoder.read_string()
            elif field_number == 18 and wire_type == WIRE_LENGTH_DELIMITED:
                result['sender'] = ResponseParser._parse_user(decoder.read_bytes())
                # sender에서 정보 추출
                if result['sender']:
                    result['senderNickname'] = result['sender'].get('nickname', '')
                    result['senderProfile'] = result['sender'].get('profileImage', '')
            elif field_number == 19 and wire_type == WIRE_LENGTH_DELIMITED:
                result['receiver'] = ResponseParser._parse_user(decoder.read_bytes())
            elif field_number == 20 and wire_type == WIRE_LENGTH_DELIMITED:
                result['imagesList'].append(ResponseParser._parse_image(decoder.read_bytes()))
            elif field_number == 21 and wire_type == WIRE_LENGTH_DELIMITED:
                result['deleteTime'] = ResponseParser._parse_timestamp(decoder.read_bytes())
            else:
                decoder.skip_field(wire_type)

        return result

    @staticmethod
    def _parse_new_message_event(data: bytes) -> Dict[str, Any]:
        """
        NewMessageEvent 파싱 (main.js 기준)

        NewMessageEvent {
            string channelId = 1;
            int64 senderId = 2;
            string senderNickname = 3;
            string senderProfile = 4;
            string content = 5;
            bool silence = 6;
            bool mute = 7;
            string targetUri = 8;
            string resourceTitle = 9;
            UnreadCount unreadCount = 10;
            string notificationSound = 13;
            int64 messageId = 14;
            User sender = 15;
            int64 bizAccountId = 16;
            Notification notification = 17;
            bool readonly = 18;
            User receiver = 19;
            string sessionId = 20;
            string collapseId = 21;
            string messageType = 22;
            int32 templateType = 23;
        }
        """
        decoder = ProtobufDecoder(data)
        result = {
            'id': '',
            'channelId': '',
            'senderId': 0,
            'senderNickname': '',
            'senderProfile': '',
            'content': '',
            'silence': False,
            'mute': False,
            'targetUri': '',
            'resourceTitle': '',
            'notificationSound': '',
            'bizAccountId': 0,
            'type': 'TEXT',
            'sender': None,
            'receiver': None,
            'notification': None,
            'readonly': False,
            'sessionId': '',
            'collapseId': '',
            'templateType': 0
        }

        while decoder.has_more():
            field_number, wire_type = decoder.read_tag()

            if field_number == 1 and wire_type == WIRE_LENGTH_DELIMITED:
                result['channelId'] = decoder.read_string()
            elif field_number == 2 and wire_type == WIRE_VARINT:
                result['senderId'] = decoder.read_int64()
            elif field_number == 3 and wire_type == WIRE_LENGTH_DELIMITED:
                result['senderNickname'] = decoder.read_string()
            elif field_number == 4 and wire_type == WIRE_LENGTH_DELIMITED:
                result['senderProfile'] = decoder.read_string()
            elif field_number == 5 and wire_type == WIRE_LENGTH_DELIMITED:
                result['content'] = decoder.read_string()
            elif field_number == 6 and wire_type == WIRE_VARINT:
                result['silence'] = decoder.read_bool()
            elif field_number == 7 and wire_type == WIRE_VARINT:
                result['mute'] = decoder.read_bool()
            elif field_number == 8 and wire_type == WIRE_LENGTH_DELIMITED:
                result['targetUri'] = decoder.read_string()
            elif field_number == 9 and wire_type == WIRE_LENGTH_DELIMITED:
                result['resourceTitle'] = decoder.read_string()
            elif field_number == 10 and wire_type == WIRE_LENGTH_DELIMITED:
                # UnreadCount - 일단 스킵
                decoder.read_bytes()
            elif field_number == 13 and wire_type == WIRE_LENGTH_DELIMITED:
                result['notificationSound'] = decoder.read_string()
            elif field_number == 14 and wire_type == WIRE_VARINT:
                result['id'] = str(decoder.read_int64())  # messageId를 id로 사용
            elif field_number == 15 and wire_type == WIRE_LENGTH_DELIMITED:
                result['sender'] = ResponseParser._parse_user(decoder.read_bytes())
            elif field_number == 16 and wire_type == WIRE_VARINT:
                result['bizAccountId'] = decoder.read_int64()
            elif field_number == 17 and wire_type == WIRE_LENGTH_DELIMITED:
                result['notification'] = ResponseParser._parse_notification(decoder.read_bytes())
            elif field_number == 18 and wire_type == WIRE_VARINT:
                result['readonly'] = decoder.read_bool()
            elif field_number == 19 and wire_type == WIRE_LENGTH_DELIMITED:
                result['receiver'] = ResponseParser._parse_user(decoder.read_bytes())
            elif field_number == 20 and wire_type == WIRE_LENGTH_DELIMITED:
                result['sessionId'] = decoder.read_string()
            elif field_number == 21 and wire_type == WIRE_LENGTH_DELIMITED:
                result['collapseId'] = decoder.read_string()
            elif field_number == 22 and wire_type == WIRE_LENGTH_DELIMITED:
                result['type'] = decoder.read_string()
            elif field_number == 23 and wire_type == WIRE_VARINT:
                result['templateType'] = decoder.read_int32()
            else:
                decoder.skip_field(wire_type)

        return result

    @staticmethod
    def _parse_notification(data: bytes) -> Dict[str, Any]:
        """
        NewMessageEvent.Notification 파싱 (main.js 기준)

        Notification {
            string summary = 1;           // 채널/채팅 제목
            string nickname = 2;          // 발신자 닉네임
            string message = 3;           // 실제 메시지 내용!
            string largeImageUrl = 4;
            bool isCircleLargeIcon = 5;
            int32 type = 6;
            string translatedPushTitle = 7;
            MessageStyleNotification messageStyleNotification = 8;
        }
        """
        decoder = ProtobufDecoder(data)
        result = {
            'title': '',      # summary -> title (채널명)
            'message': '',    # 실제 메시지 내용
            'nickname': '',
            'largeImageUrl': '',
            'isCircleLargeIcon': False,
            'type': 0,
            'translatedPushTitle': ''
        }

        while decoder.has_more():
            field_number, wire_type = decoder.read_tag()
            if field_number == 1 and wire_type == WIRE_LENGTH_DELIMITED:
                result['title'] = decoder.read_string()  # summary -> title
            elif field_number == 2 and wire_type == WIRE_LENGTH_DELIMITED:
                result['nickname'] = decoder.read_string()
            elif field_number == 3 and wire_type == WIRE_LENGTH_DELIMITED:
                result['message'] = decoder.read_string()  # 실제 메시지!
            elif field_number == 4 and wire_type == WIRE_LENGTH_DELIMITED:
                result['largeImageUrl'] = decoder.read_string()
            elif field_number == 5 and wire_type == WIRE_VARINT:
                result['isCircleLargeIcon'] = decoder.read_bool()
            elif field_number == 6 and wire_type == WIRE_VARINT:
                result['type'] = decoder.read_int32()
            elif field_number == 7 and wire_type == WIRE_LENGTH_DELIMITED:
                result['translatedPushTitle'] = decoder.read_string()
            else:
                decoder.skip_field(wire_type)

        return result

    @staticmethod
    def _parse_user(data: bytes) -> Dict[str, Any]:
        """
        User 메시지 파싱 (main.js 기준)

        User {
            int64 id = 1;
            string nickname = 2;
            string displayRegionName = 3;
            string profileImage = 4;
            float temperature = 5;
            string messageResponseTime = 6;
            bool isDoNotDisturbOn = 7;
            string doNotDisturbStartTime = 8;
            string doNotDisturbEndTime = 9;
            string badgeImage = 10;
            repeated int32 userFlaggedByMeList = 11;
            string status = 12;
            string targetUri = 13;
            int32 type = 14;
            int32 displayRegionCheckinsCount = 15;
            string doNotDisturbeTimeZone = 16;
            Region region = 17;
            bool isVerified = 18;
            string displayLocationName = 19;
            bool isBizFollower = 20;
            bool isSameCondoMember = 21;
            string subnickname = 22;
            int32 role = 23;
            float mannerTemperature = 101;
            KarrotScore karrotScore = 102;
        }
        """
        decoder = ProtobufDecoder(data)
        result = {
            'id': 0,
            'nickname': '',
            'displayRegionName': '',
            'profileImage': '',
            'temperature': 0.0,
            'messageResponseTime': '',
            'isDoNotDisturbOn': False,
            'badgeImage': '',
            'status': '',
            'targetUri': '',
            'type': 1,
            'isVerified': False,
            'displayLocationName': '',
            'subnickname': '',
            'role': 0,
            'mannerTemperature': 36.5
        }

        while decoder.has_more():
            field_number, wire_type = decoder.read_tag()

            if field_number == 1 and wire_type == WIRE_VARINT:
                result['id'] = decoder.read_int64()
            elif field_number == 2 and wire_type == WIRE_LENGTH_DELIMITED:
                result['nickname'] = decoder.read_string()
            elif field_number == 3 and wire_type == WIRE_LENGTH_DELIMITED:
                result['displayRegionName'] = decoder.read_string()
            elif field_number == 4 and wire_type == WIRE_LENGTH_DELIMITED:
                result['profileImage'] = decoder.read_string()
            elif field_number == 5 and wire_type == WIRE_FIXED32:
                result['temperature'] = decoder.read_float()
            elif field_number == 6 and wire_type == WIRE_LENGTH_DELIMITED:
                result['messageResponseTime'] = decoder.read_string()
            elif field_number == 7 and wire_type == WIRE_VARINT:
                result['isDoNotDisturbOn'] = decoder.read_bool()
            elif field_number == 10 and wire_type == WIRE_LENGTH_DELIMITED:
                result['badgeImage'] = decoder.read_string()
            elif field_number == 12 and wire_type == WIRE_LENGTH_DELIMITED:
                result['status'] = decoder.read_string()
            elif field_number == 13 and wire_type == WIRE_LENGTH_DELIMITED:
                result['targetUri'] = decoder.read_string()
            elif field_number == 14 and wire_type == WIRE_VARINT:
                result['type'] = decoder.read_int32()
            elif field_number == 18 and wire_type == WIRE_VARINT:
                result['isVerified'] = decoder.read_bool()
            elif field_number == 19 and wire_type == WIRE_LENGTH_DELIMITED:
                result['displayLocationName'] = decoder.read_string()
            elif field_number == 22 and wire_type == WIRE_LENGTH_DELIMITED:
                result['subnickname'] = decoder.read_string()
            elif field_number == 23 and wire_type == WIRE_VARINT:
                result['role'] = decoder.read_int32()
            elif field_number == 101 and wire_type == WIRE_FIXED32:
                result['mannerTemperature'] = decoder.read_float()
            else:
                decoder.skip_field(wire_type)

        return result

    @staticmethod
    def _parse_biz_account(data: bytes) -> Dict[str, Any]:
        """BizAccount 파싱"""
        decoder = ProtobufDecoder(data)
        result = {
            'id': 0,
            'name': '',
            'imageUrl': '',
            'category': '',
            'region': ''
        }

        while decoder.has_more():
            field_number, wire_type = decoder.read_tag()

            if field_number == 1 and wire_type == WIRE_VARINT:
                result['id'] = decoder.read_int64()
            elif field_number == 2 and wire_type == WIRE_LENGTH_DELIMITED:
                result['name'] = decoder.read_string()
            elif field_number == 3 and wire_type == WIRE_LENGTH_DELIMITED:
                result['imageUrl'] = decoder.read_string()
            elif field_number == 4 and wire_type == WIRE_LENGTH_DELIMITED:
                result['category'] = decoder.read_string()
            elif field_number == 5 and wire_type == WIRE_LENGTH_DELIMITED:
                result['region'] = decoder.read_string()
            else:
                decoder.skip_field(wire_type)

        return result

    @staticmethod
    def _parse_sticker(data: bytes) -> Dict[str, Any]:
        """Sticker 파싱"""
        decoder = ProtobufDecoder(data)
        result = {'id': '', 'imageUrl': '', 'name': ''}

        while decoder.has_more():
            field_number, wire_type = decoder.read_tag()
            if field_number == 1 and wire_type == WIRE_LENGTH_DELIMITED:
                result['id'] = decoder.read_string()
            elif field_number == 2 and wire_type == WIRE_LENGTH_DELIMITED:
                result['imageUrl'] = decoder.read_string()
            elif field_number == 3 and wire_type == WIRE_LENGTH_DELIMITED:
                result['name'] = decoder.read_string()
            else:
                decoder.skip_field(wire_type)

        return result

    @staticmethod
    def _parse_member(data: bytes) -> Dict[str, Any]:
        """Member 메시지 파싱"""
        decoder = ProtobufDecoder(data)
        result = {
            'id': 0,
            'nickname': '',
            'profileImage': '',
            'isHost': False
        }

        while decoder.has_more():
            field_number, wire_type = decoder.read_tag()

            if field_number == 1 and wire_type == WIRE_VARINT:
                result['id'] = decoder.read_int64()
            elif field_number == 2 and wire_type == WIRE_LENGTH_DELIMITED:
                result['nickname'] = decoder.read_string()
            elif field_number == 3 and wire_type == WIRE_LENGTH_DELIMITED:
                result['profileImage'] = decoder.read_string()
            elif field_number == 4 and wire_type == WIRE_VARINT:
                result['isHost'] = decoder.read_bool()
            else:
                decoder.skip_field(wire_type)

        return result

    @staticmethod
    def _parse_image(data: bytes) -> Dict[str, Any]:
        """Image 메시지 파싱"""
        decoder = ProtobufDecoder(data)
        result = {
            'id': '',
            'url': '',
            'width': 0,
            'height': 0,
            'thumbnailUrl': ''
        }

        while decoder.has_more():
            field_number, wire_type = decoder.read_tag()

            if field_number == 1 and wire_type == WIRE_LENGTH_DELIMITED:
                result['id'] = decoder.read_string()
            elif field_number == 2 and wire_type == WIRE_LENGTH_DELIMITED:
                result['url'] = decoder.read_string()
            elif field_number == 3 and wire_type == WIRE_VARINT:
                result['width'] = decoder.read_int32()
            elif field_number == 4 and wire_type == WIRE_VARINT:
                result['height'] = decoder.read_int32()
            elif field_number == 5 and wire_type == WIRE_LENGTH_DELIMITED:
                result['thumbnailUrl'] = decoder.read_string()
            else:
                decoder.skip_field(wire_type)

        return result

    @staticmethod
    def _parse_timestamp(data: bytes) -> Dict[str, Any]:
        """Timestamp 메시지 파싱"""
        decoder = ProtobufDecoder(data)
        result = {'seconds': 0, 'nanos': 0}

        while decoder.has_more():
            field_number, wire_type = decoder.read_tag()

            if field_number == 1 and wire_type == WIRE_VARINT:
                result['seconds'] = decoder.read_int64()
            elif field_number == 2 and wire_type == WIRE_VARINT:
                result['nanos'] = decoder.read_int32()
            else:
                decoder.skip_field(wire_type)

        return result

    @staticmethod
    def _parse_paging_key(data: bytes) -> Dict[str, Any]:
        """PagingKey 메시지 파싱"""
        decoder = ProtobufDecoder(data)
        result = {'kind': 0, 'time': None}

        while decoder.has_more():
            field_number, wire_type = decoder.read_tag()

            if field_number == 1 and wire_type == WIRE_VARINT:
                result['kind'] = decoder.read_int32()
            elif field_number == 2 and wire_type == WIRE_LENGTH_DELIMITED:
                result['time'] = ResponseParser._parse_timestamp(decoder.read_bytes())
            else:
                decoder.skip_field(wire_type)

        return result

    @staticmethod
    def _parse_read_event(data: bytes) -> Dict[str, Any]:
        """ReadEvent 메시지 파싱"""
        decoder = ProtobufDecoder(data)
        result = {'channelId': '', 'messageId': '', 'userId': 0}

        while decoder.has_more():
            field_number, wire_type = decoder.read_tag()

            if field_number == 1 and wire_type == WIRE_LENGTH_DELIMITED:
                result['channelId'] = decoder.read_string()
            elif field_number == 2 and wire_type == WIRE_VARINT:
                result['messageId'] = str(decoder.read_int64())
            elif field_number == 3 and wire_type == WIRE_VARINT:
                result['userId'] = decoder.read_int64()
            else:
                decoder.skip_field(wire_type)

        return result

    @staticmethod
    def _parse_member_event(data: bytes) -> Dict[str, Any]:
        """MemberEvent 메시지 파싱 (Join/Leave)"""
        decoder = ProtobufDecoder(data)
        result = {'channelId': '', 'member': None}

        while decoder.has_more():
            field_number, wire_type = decoder.read_tag()

            if field_number == 1 and wire_type == WIRE_LENGTH_DELIMITED:
                result['channelId'] = decoder.read_string()
            elif field_number == 2 and wire_type == WIRE_LENGTH_DELIMITED:
                result['member'] = ResponseParser._parse_user(decoder.read_bytes())
            else:
                decoder.skip_field(wire_type)

        return result

    @staticmethod
    def _parse_renew_channel_event(data: bytes) -> Dict[str, Any]:
        """RenewChannelEvent 파싱"""
        decoder = ProtobufDecoder(data)
        result = {'channel': None}

        while decoder.has_more():
            field_number, wire_type = decoder.read_tag()
            if field_number == 1 and wire_type == WIRE_LENGTH_DELIMITED:
                result['channel'] = ResponseParser._parse_channel(decoder.read_bytes())
            else:
                decoder.skip_field(wire_type)

        return result

    @staticmethod
    def _parse_update_message_event(data: bytes) -> Dict[str, Any]:
        """UpdateMessageEvent 파싱"""
        decoder = ProtobufDecoder(data)
        result = {'message': None}

        while decoder.has_more():
            field_number, wire_type = decoder.read_tag()
            if field_number == 1 and wire_type == WIRE_LENGTH_DELIMITED:
                result['message'] = ResponseParser._parse_message(decoder.read_bytes())
            else:
                decoder.skip_field(wire_type)

        return result

    @staticmethod
    def _parse_persistent_menu(data: bytes) -> Dict[str, Any]:
        """PersistentMenu 메시지 파싱"""
        decoder = ProtobufDecoder(data)
        result = {'itemsList': []}

        while decoder.has_more():
            field_number, wire_type = decoder.read_tag()

            if field_number == 1 and wire_type == WIRE_LENGTH_DELIMITED:
                result['itemsList'].append(decoder.read_string())
            else:
                decoder.skip_field(wire_type)

        return result
