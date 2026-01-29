# PNS AI SDK for Python

PNS AI Hub 서비스를 쉽게 사용할 수 있는 Python SDK입니다.

## 설치

```bash
pip install pnslab-ai-sdk
```

## 빠른 시작

```python
from pns_ai import AIClient

# 클라이언트 생성
client = AIClient(
    api_key="pns_sk_live_xxx",      # API 키
    encryption_key="your_64_hex"     # 암호화 키
)

# AI와 대화
response = client.chat("안녕하세요!")
print(response.text)
```

## 스트리밍

```python
# 실시간 스트리밍 응답
for chunk in client.chat_stream("긴 이야기를 해줘"):
    print(chunk, end="", flush=True)
```

## 모델 선택

```python
# Claude Sonnet 4.5 (기본값, 가장 추천)
response = client.chat("질문", model="claude-sonnet-4.5")

# Nova Lite (빠른 응답)
response = client.chat("질문", model="nova-lite")
```

## 옵션 설정

```python
response = client.chat(
    message="창의적인 이야기를 해줘",
    model="claude-sonnet-4.5",
    max_tokens=2000,        # 최대 응답 길이
    temperature=0.9,        # 창의성 (0.0~1.0)
    system="당신은 창의적인 작가입니다"  # 시스템 프롬프트
)
```

## 사용량 확인

```python
usage = client.get_usage()
print(f"이번 달 사용: {usage['currentMonthTokens']:,} 토큰")
print(f"남은 토큰: {usage['remainingTokens']:,}")
```

## 에러 처리

```python
from pns_ai import AIClient, AuthenticationError, TokenLimitError

try:
    response = client.chat("안녕")
except AuthenticationError:
    print("API 키가 올바르지 않습니다")
except TokenLimitError:
    print("이번 달 토큰 한도를 초과했습니다")
```

## API 키 발급

API 키는 [PNS Portal](https://pns-lab.com)에서 발급받을 수 있습니다.

## 라이선스

MIT License
