# Web Player

웹 브라우저를 통한 원격 데스크톱 제어 시스템

## Quick Start

```bash
# Install
git clone git@github.com:seunghyun-kim-bagel/web-player.git
cd web-player
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Run
python run.py
```

브라우저에서 http://localhost:8000 접속

## Features

- 실시간 화면 스트리밍 (30 FPS)
- 마우스 제어: 클릭, 더블클릭, 우클릭, 드래그
- 키보드 제어: 텍스트 입력, 단축키 (Ctrl+C 등)
- 스크롤 지원

## Usage

| Action | How |
|--------|-----|
| Click | Canvas 클릭 |
| Double Click | 빠르게 두 번 클릭 |
| Right Click | 우클릭 |
| Drag | 누르고 이동 |
| Scroll | 마우스 휠 |
| Keyboard | 화면 포커스 후 타이핑 |

## Project Structure

```
web-player/
├── src/server/          # FastAPI 백엔드
│   ├── main.py          # WebSocket 엔드포인트
│   ├── screen_controller.py
│   └── action_handler.py
├── static/              # 프론트엔드
│   ├── index.html
│   ├── css/
│   └── js/
├── docs/
│   └── TECHNICAL.md     # 기술 문서
├── run.py
└── requirements.txt
```

## Requirements

- Python 3.10+
- macOS / Windows / Linux

## Documentation

상세 기술 문서: [docs/TECHNICAL.md](docs/TECHNICAL.md)

## License

MIT
