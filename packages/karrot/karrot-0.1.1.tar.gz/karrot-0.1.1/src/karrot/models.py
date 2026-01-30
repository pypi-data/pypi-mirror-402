"""
Karrot Chat Library - Models
당근마켓 채팅 관련 데이터 모델 정의
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any, TYPE_CHECKING

from .enums import MessageType, ChannelType, UserType, Status

if TYPE_CHECKING:
    from .client import Client


@dataclass
class Timestamp:
    """타임스탬프"""
    seconds: int = 0
    nanos: int = 0

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional['Timestamp']:
        if not data:
            return None
        return cls(
            seconds=data.get('seconds', 0),
            nanos=data.get('nanos', 0)
        )

    def to_datetime(self) -> datetime:
        """datetime 객체로 변환"""
        return datetime.fromtimestamp(self.seconds + self.nanos / 1e9)

    def to_dict(self) -> Dict[str, Any]:
        return {'seconds': self.seconds, 'nanos': self.nanos}


@dataclass
class Image:
    """이미지 정보"""
    id: str = ""
    url: str = ""
    width: int = 0
    height: int = 0
    thumbnail_url: str = ""

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional['Image']:
        if not data:
            return None
        return cls(
            id=data.get('id', ''),
            url=data.get('url', ''),
            width=data.get('width', 0),
            height=data.get('height', 0),
            thumbnail_url=data.get('thumbnailUrl', '')
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'url': self.url,
            'width': self.width,
            'height': self.height,
            'thumbnailUrl': self.thumbnail_url
        }


@dataclass
class User:
    """
    사용자 정보 (main.js 기준)

    User {
        int64 id = 1;
        string nickname = 2;
        string displayRegionName = 3;
        string profileImage = 4;
        float temperature = 5;
        string messageResponseTime = 6;
        bool isDoNotDisturbOn = 7;
        string badgeImage = 10;
        string status = 12;
        string targetUri = 13;
        int32 type = 14;
        bool isVerified = 18;
        string displayLocationName = 19;
        string subnickname = 22;
        int32 role = 23;
        float mannerTemperature = 101;
    }
    """
    id: int = 0
    nickname: str = ""
    profile_image: str = ""
    type: UserType = UserType.NORMAL
    display_region_name: str = ""
    temperature: float = 0.0
    message_response_time: str = ""
    is_do_not_disturb_on: bool = False
    badge_image: str = ""
    status: str = ""
    target_uri: str = ""
    is_verified: bool = False
    display_location_name: str = ""
    subnickname: str = ""
    role: int = 0
    manner_temperature: float = 36.5

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional['User']:
        if not data:
            return None

        # UserType 안전하게 파싱
        type_val = data.get('type', 0)
        try:
            user_type = UserType(type_val) if type_val in UserType._value2member_map_ else UserType.UNKNOWN
        except (ValueError, KeyError):
            user_type = UserType.UNKNOWN

        return cls(
            id=data.get('id', 0),
            nickname=data.get('nickname', ''),
            profile_image=data.get('profileImage', data.get('profileUrl', '')),
            type=user_type,
            display_region_name=data.get('displayRegionName', ''),
            temperature=data.get('temperature', 0.0),
            message_response_time=data.get('messageResponseTime', ''),
            is_do_not_disturb_on=data.get('isDoNotDisturbOn', False),
            badge_image=data.get('badgeImage', ''),
            status=data.get('status', ''),
            target_uri=data.get('targetUri', ''),
            is_verified=data.get('isVerified', False),
            display_location_name=data.get('displayLocationName', ''),
            subnickname=data.get('subnickname', ''),
            role=data.get('role', 0),
            manner_temperature=data.get('mannerTemperature', 36.5)
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'nickname': self.nickname,
            'profileImage': self.profile_image,
            'type': self.type.value,
            'displayRegionName': self.display_region_name,
            'temperature': self.temperature,
            'messageResponseTime': self.message_response_time,
            'isDoNotDisturbOn': self.is_do_not_disturb_on,
            'badgeImage': self.badge_image,
            'status': self.status,
            'targetUri': self.target_uri,
            'isVerified': self.is_verified,
            'displayLocationName': self.display_location_name,
            'subnickname': self.subnickname,
            'role': self.role,
            'mannerTemperature': self.manner_temperature
        }

    @property
    def name(self) -> str:
        """닉네임의 별칭"""
        return self.nickname

    @property
    def region(self) -> str:
        """지역명 (displayRegionName의 별칭)"""
        return self.display_region_name

    def __str__(self) -> str:
        return f"User(id={self.id}, nickname='{self.nickname}')"


@dataclass
class BizAccount:
    """비즈니스 계정 정보"""
    id: int = 0
    name: str = ""
    image_url: str = ""
    category: str = ""
    region: str = ""

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional['BizAccount']:
        if not data:
            return None
        return cls(
            id=data.get('id', 0),
            name=data.get('name', ''),
            image_url=data.get('imageUrl', ''),
            category=data.get('category', ''),
            region=data.get('region', '')
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'imageUrl': self.image_url,
            'category': self.category,
            'region': self.region
        }


@dataclass
class Member:
    """채널 멤버 정보"""
    id: int = 0
    nickname: str = ""
    profile_image: str = ""
    is_host: bool = False
    joined_at: Optional[Timestamp] = None

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional['Member']:
        if not data:
            return None
        return cls(
            id=data.get('id', 0),
            nickname=data.get('nickname', ''),
            profile_image=data.get('profileImage', ''),
            is_host=data.get('isHost', False),
            joined_at=Timestamp.from_dict(data.get('joinedAt'))
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'nickname': self.nickname,
            'profileImage': self.profile_image,
            'isHost': self.is_host,
            'joinedAt': self.joined_at.to_dict() if self.joined_at else None
        }


@dataclass
class Sticker:
    """스티커 정보"""
    id: str = ""
    image_url: str = ""
    name: str = ""

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional['Sticker']:
        if not data:
            return None
        return cls(
            id=data.get('id', ''),
            image_url=data.get('imageUrl', ''),
            name=data.get('name', '')
        )


@dataclass
class Notification:
    """
    알림 정보 (main.js NewMessageEvent.Notification 기준)

    - title: 채널/채팅 제목 (summary)
    - nickname: 발신자 닉네임
    - message: 실제 메시지 내용
    - large_image_url: 큰 이미지 URL
    - is_circle_large_icon: 원형 아이콘 여부
    - type: 알림 타입
    - translated_push_title: 번역된 푸시 제목
    """
    message: str = ""
    title: str = ""
    nickname: str = ""
    large_image_url: str = ""
    is_circle_large_icon: bool = False
    type: int = 0
    translated_push_title: str = ""

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional['Notification']:
        if not data:
            return None
        return cls(
            message=data.get('message', ''),
            title=data.get('title', ''),
            nickname=data.get('nickname', ''),
            large_image_url=data.get('largeImageUrl', ''),
            is_circle_large_icon=data.get('isCircleLargeIcon', False),
            type=data.get('type', 0),
            translated_push_title=data.get('translatedPushTitle', '')
        )


@dataclass
class Message:
    """메시지 정보"""
    id: str = ""
    channel_id: str = ""
    content: str = ""
    type: MessageType = MessageType.TEXT
    sender_id: int = 0
    sender_nickname: str = ""
    sender_profile: str = ""
    sender: Optional[User] = None
    receiver: Optional[User] = None
    images: List[Image] = field(default_factory=list)
    created_at: Optional[Timestamp] = None
    updated_at: Optional[Timestamp] = None
    is_deleted: bool = False
    is_read: bool = False
    silence: bool = False
    biz_account_id: int = 0
    notification: Optional[Notification] = None

    # 내부 참조
    _client: Optional['Client'] = field(default=None, repr=False)
    _channel: Optional['Channel'] = field(default=None, repr=False)

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]], client: Optional['Client'] = None) -> Optional['Message']:
        if not data:
            return None

        # 메시지 타입 파싱
        type_str = data.get('type', '')
        msg_type = MessageType.TEXT
        if type_str == 'TEXT':
            msg_type = MessageType.TEXT
        elif type_str == 'IMAG':
            msg_type = MessageType.IMAGE
        elif type_str == 'STIC':
            msg_type = MessageType.STICKER
        elif type_str == 'GALL':
            msg_type = MessageType.GALLERY
        elif type_str == 'SYST':
            msg_type = MessageType.SYSTEM
        elif type_str == 'DELT':
            msg_type = MessageType.DELETED
        elif type_str == 'TEMP':
            msg_type = MessageType.TEMPLATE
        elif isinstance(type_str, int):
            msg_type = MessageType(type_str) if type_str in MessageType._value2member_map_ else MessageType.TEXT

        images = []
        images_list = data.get('imagesList', [])
        for img_data in images_list:
            img = Image.from_dict(img_data)
            if img:
                images.append(img)

        return cls(
            id=data.get('id', data.get('messageId', '')),
            channel_id=data.get('channelId', ''),
            content=data.get('content', ''),
            type=msg_type,
            sender_id=data.get('senderId', 0),
            sender_nickname=data.get('senderNickname', ''),
            sender_profile=data.get('senderProfile', ''),
            sender=User.from_dict(data.get('sender')),
            receiver=User.from_dict(data.get('receiver')),
            images=images,
            created_at=Timestamp.from_dict(data.get('createdAt')),
            updated_at=Timestamp.from_dict(data.get('updatedAt')),
            is_deleted=data.get('isDeleted', False),
            is_read=data.get('isRead', False),
            silence=data.get('silence', False),
            biz_account_id=data.get('bizAccountId', 0),
            notification=Notification.from_dict(data.get('notification')),
            _client=client
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'channelId': self.channel_id,
            'content': self.content,
            'type': self.type.name,
            'senderId': self.sender_id,
            'senderNickname': self.sender_nickname,
            'senderProfile': self.sender_profile,
            'sender': self.sender.to_dict() if self.sender else None,
            'receiver': self.receiver.to_dict() if self.receiver else None,
            'imagesList': [img.to_dict() for img in self.images],
            'createdAt': self.created_at.to_dict() if self.created_at else None,
            'updatedAt': self.updated_at.to_dict() if self.updated_at else None,
            'isDeleted': self.is_deleted,
            'isRead': self.is_read,
            'silence': self.silence,
            'bizAccountId': self.biz_account_id
        }

    @property
    def channel(self) -> Optional['Channel']:
        """메시지가 속한 채널"""
        return self._channel

    @property
    def text(self) -> str:
        """순수 메시지 내용 (발신자 닉네임 제외)

        content는 '닉네임 : 메시지' 형태로 되어있어서,
        notification.message 또는 content에서 닉네임 부분을 제거한 값을 반환합니다.
        """
        # notification.message가 있으면 그것이 순수 메시지
        if self.notification and self.notification.message:
            return self.notification.message

        # notification이 없으면 content에서 닉네임 부분 제거 시도
        if self.content and self.sender_nickname:
            prefix = f"{self.sender_nickname} : "
            if self.content.startswith(prefix):
                return self.content[len(prefix):]

        # 둘 다 없으면 원본 content 반환
        return self.content

    @property
    def author(self) -> Optional[User]:
        """메시지 작성자 (sender의 별칭)"""
        return self.sender

    @property
    def user(self) -> Optional[User]:
        """메시지 작성자 (sender의 별칭)"""
        return self.sender

    async def reply(self, content: str) -> Optional['Message']:
        """메시지에 답장"""
        if self._channel:
            return await self._channel.send(content)
        elif self._client and self.channel_id:
            return await self._client.send_message(self.channel_id, content)
        return None

    def __str__(self) -> str:
        return f"Message(id='{self.id}', content='{self.content[:20]}...')" if len(self.content) > 20 else f"Message(id='{self.id}', content='{self.content}')"


@dataclass
class PagingKey:
    """페이징 키"""
    kind: int = 0
    time: Optional[Timestamp] = None

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional['PagingKey']:
        if not data:
            return None
        return cls(
            kind=data.get('kind', 0),
            time=Timestamp.from_dict(data.get('time'))
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'kind': self.kind,
            'time': self.time.to_dict() if self.time else None
        }


@dataclass
class UnreadCount:
    """읽지 않은 메시지 수"""
    total: int = 0
    by_channel: Dict[str, int] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional['UnreadCount']:
        if not data:
            return None
        return cls(
            total=data.get('total', 0),
            by_channel=data.get('byChannel', {})
        )


@dataclass
class Channel:
    """
    채널 정보 (main.js 기준)

    Channel {
        string id = 1;
        string resourceType = 2;
        int64 resourceId = 3;
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
        User me = 23;
        BizAccount bizAccount = 24;
        string targetUri = 26;
        int32 type = 27;
        repeated User membersList = 28;
        User owner = 29;
        string title = 30;
        string thumbnail = 31;
        int32 memberLimit = 33;
        bool closed = 34;
        bool isTemporary = 39;
        int32 unreadMentionsCount = 41;
        int32 memberCount = 42;
        int64 lastMessageId = 52;
    }
    """
    id: str = ""
    type: ChannelType = ChannelType.DIRECT
    name: str = ""
    image_url: str = ""
    member_count: int = 0
    unread_count: int = 0
    last_message: Optional[Message] = None
    last_message_id: str = ""
    last_read_message_id: str = ""
    members: List[Member] = field(default_factory=list)
    me: Optional[Member] = None
    receiver: Optional[User] = None
    owner: Optional[User] = None
    resource_type: str = ""
    resource_id: int = 0
    target_uri: str = ""
    is_muted: bool = False
    is_blocked: bool = False
    is_favorite: bool = False
    is_read_only: bool = False
    is_disabled: bool = False
    is_temporary: bool = False
    closed: bool = False
    member_limit: int = 0
    unread_mentions_count: int = 0
    created_at: Optional[Timestamp] = None
    updated_at: Optional[Timestamp] = None
    biz_account: Optional[BizAccount] = None

    # 내부 참조
    _client: Optional['Client'] = field(default=None, repr=False)

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]], client: Optional['Client'] = None) -> Optional['Channel']:
        if not data:
            return None

        # 멤버 목록 파싱 (User 형식으로 오므로 Member로 변환)
        members = []
        members_list = data.get('membersList', [])
        for member_data in members_list:
            # User 형식을 Member로 변환
            member = Member(
                id=member_data.get('id', 0),
                nickname=member_data.get('nickname', ''),
                profile_image=member_data.get('profileImage', ''),
                is_host=False
            )
            members.append(member)

        # 채널 타입 파싱
        channel_type = ChannelType.DIRECT
        type_val = data.get('type', 0)
        if isinstance(type_val, int) and type_val in ChannelType._value2member_map_:
            channel_type = ChannelType(type_val)

        # lastMessageId 처리 (int -> str)
        last_message_id = data.get('lastMessageId', '')
        if isinstance(last_message_id, int):
            last_message_id = str(last_message_id)

        return cls(
            id=data.get('id', ''),
            type=channel_type,
            name=data.get('name', ''),
            image_url=data.get('imageUrl', ''),
            member_count=data.get('memberCount', 0),
            unread_count=data.get('unreadCount', 0),
            last_message=Message.from_dict(data.get('lastMessage'), client),
            last_message_id=last_message_id,
            last_read_message_id=data.get('lastReadMessageId', ''),
            members=members,
            me=Member(
                id=data.get('me', {}).get('id', 0) if data.get('me') else 0,
                nickname=data.get('me', {}).get('nickname', '') if data.get('me') else '',
                profile_image=data.get('me', {}).get('profileImage', '') if data.get('me') else '',
                is_host=False
            ) if data.get('me') else None,
            receiver=User.from_dict(data.get('receiver')),
            owner=User.from_dict(data.get('owner')),
            resource_type=data.get('resourceType', ''),
            resource_id=data.get('resourceId', 0),
            target_uri=data.get('targetUri', ''),
            is_muted=data.get('isMuted', False),
            is_blocked=data.get('isBlocked', False),
            is_favorite=data.get('isFavorite', False),
            is_read_only=data.get('isReadOnly', False),
            is_disabled=data.get('isDisabled', False),
            is_temporary=data.get('isTemporary', False),
            closed=data.get('closed', False),
            member_limit=data.get('memberLimit', 0),
            unread_mentions_count=data.get('unreadMentionsCount', 0),
            created_at=Timestamp.from_dict(data.get('createTime')),
            updated_at=Timestamp.from_dict(data.get('lastMessageTime')),
            biz_account=BizAccount.from_dict(data.get('bizAccount')),
            _client=client
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'type': self.type.value,
            'name': self.name,
            'imageUrl': self.image_url,
            'memberCount': self.member_count,
            'unreadCount': self.unread_count,
            'lastMessage': self.last_message.to_dict() if self.last_message else None,
            'lastMessageId': self.last_message_id,
            'lastReadMessageId': self.last_read_message_id,
            'membersList': [m.to_dict() for m in self.members],
            'me': self.me.to_dict() if self.me else None,
            'resourceType': self.resource_type,
            'resourceId': self.resource_id,
            'isMuted': self.is_muted,
            'isBlocked': self.is_blocked,
            'isFavorite': self.is_favorite,
            'createdAt': self.created_at.to_dict() if self.created_at else None,
            'updatedAt': self.updated_at.to_dict() if self.updated_at else None
        }

    @property
    def display_name(self) -> str:
        """
        표시용 채널 이름

        - 그룹 채팅: name (title) 사용
        - 1:1 채팅: receiver 닉네임 사용
        - 비즈니스: biz_account 이름 사용
        - 모두 없으면: 채널 ID의 일부
        """
        # 이름이 있으면 그대로 사용
        if self.name:
            return self.name

        # 1:1 채팅이면 상대방 닉네임 사용
        if self.type == ChannelType.DIRECT and self.receiver:
            return self.receiver.nickname or self.receiver.name

        # 비즈니스 채팅이면 비즈 계정 이름 사용
        if self.biz_account and self.biz_account.name:
            return self.biz_account.name

        # 멤버 중 나를 제외한 첫 번째 멤버 닉네임
        if self.members and self.me:
            for member in self.members:
                if member.id != self.me.id:
                    return member.nickname

        # 마지막 메시지 발신자 닉네임
        if self.last_message and self.last_message.sender_nickname:
            return self.last_message.sender_nickname

        # 모두 없으면 채널 ID의 일부
        return self.id[:15] if len(self.id) > 15 else self.id

    @property
    def title(self) -> str:
        """display_name의 별칭"""
        return self.display_name

    async def send(self, content: str) -> Optional[Message]:
        """채널에 메시지 전송"""
        if self._client:
            return await self._client.send_message(self.id, content)
        return None

    async def fetch_messages(self, limit: int = 20) -> List[Message]:
        """채널의 메시지 목록 조회"""
        if self._client:
            return await self._client.get_messages(self.id, limit=limit)
        return []

    async def mark_as_read(self) -> bool:
        """채널의 메시지를 읽음 처리"""
        if self._client:
            return await self._client.mark_as_read(self.id)
        return False

    async def leave(self) -> bool:
        """채널 나가기"""
        if self._client:
            return await self._client.leave_channel(self.id)
        return False

    def __str__(self) -> str:
        return f"Channel(id='{self.id}', name='{self.name}')"


@dataclass
class ReadEvent:
    """읽음 이벤트"""
    channel_id: str = ""
    message_id: str = ""
    user_id: int = 0

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional['ReadEvent']:
        if not data:
            return None
        return cls(
            channel_id=data.get('channelId', ''),
            message_id=data.get('messageId', ''),
            user_id=data.get('userId', 0)
        )


@dataclass
class MemberEvent:
    """멤버 이벤트"""
    channel_id: str = ""
    member: Optional[Member] = None

    # 내부 참조
    _client: Optional['Client'] = field(default=None, repr=False)
    _channel: Optional['Channel'] = field(default=None, repr=False)

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]], client: Optional['Client'] = None) -> Optional['MemberEvent']:
        if not data:
            return None
        return cls(
            channel_id=data.get('channelId', ''),
            member=Member.from_dict(data.get('member')),
            _client=client
        )

    @property
    def channel(self) -> Optional['Channel']:
        """이벤트가 발생한 채널"""
        if self._channel:
            return self._channel
        if self._client:
            return self._client.get_channel_by_id(self.channel_id)
        return None

    async def get_channel(self) -> Optional['Channel']:
        """채널 정보 조회"""
        if self._client:
            return await self._client.get_channel(self.channel_id)
        return None

    async def send(self, content: str) -> Optional[Message]:
        """해당 채널에 메시지 전송"""
        if self._client:
            return await self._client.send_message(self.channel_id, content)
        return None
