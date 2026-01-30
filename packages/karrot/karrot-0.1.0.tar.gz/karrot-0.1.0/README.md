# karrot.py

Discord.py 스타일의 당근마켓 채팅 비동기 라이브러리

## 설치

```bash
pip install aiohttp websockets
```

## 사용법

```python
import asyncio
from karrot import Client, Message

client = Client(command_prefix="!")

@client.event
async def on_ready():
    print(f"로그인: {client.user_id}")

@client.event
async def on_message(message: Message):
    print(f"[{message.sender_nickname}] {message.text}")

    # 자신의 메시지에만 명령어 처리
    if message.sender_id == client.user_id:
        await client.process_commands(message)

@client.command("안녕", aliases=["hi", "hello"])
async def hello_command(message: Message, args: str):
    await message.reply("안녕하세요!")

@client.command("도움말", aliases=["help", "?"])
async def help_command(message: Message, args: str):
    help_text = """
📋 명령어 목록
!안녕 - 인사
!도움말 - 도움말
    """
    await message.reply(help_text)

client.run("YOUR_TOKEN_HERE")
```

## 주요 기능

### Client

```python
client = Client(
    command_prefix="!",  # 명령어 접두사
    region="kr",         # 지역 (kr, jp, ca, uk, us)
    auto_reconnect=True  # 자동 재연결
)
```

### 이벤트

- `on_ready()` - 연결 완료
- `on_message(message)` - 새 메시지
- `on_notification(notification)` - 알림
- `on_disconnect()` - 연결 해제

### 명령어

```python
@client.command("명령어", aliases=["별칭1", "별칭2"], description="설명")
async def my_command(message: Message, args: str):
    # args: 명령어 뒤의 인자 (예: "!명령어 인자" -> args = "인자")
    await message.reply("응답")
```

### 메시지

```python
# 답장
await message.reply("텍스트")

# 채널로 전송
await client.send_message(channel_id, "텍스트")
```

### 채널

```python
# 모든 채널
channels = client.channels

# ID로 채널 찾기
channel = client.get_channel_by_id(channel_id)

# 채널 정보
channel.display_name  # 표시 이름
channel.type          # ChannelType.DIRECT 또는 ChannelType.GROUP
```

## 토큰 얻기

1. 당근마켓 웹 (https://karrotmarket.com) 로그인
2. 개발자 도구 (F12) → Network 탭
3. `chat.daangn` 요청 찾기
4. Request Headers에서 `Authorization: Bearer ...` 값 복사

## 라이선스

MIT
