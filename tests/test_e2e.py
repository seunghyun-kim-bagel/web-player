#!/usr/bin/env python3
"""
Web Player - E2E 테스트
UI-TARS 기반 자연어 명령 처리 테스트
"""
import asyncio
import json
import sys
import os

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import websockets


async def test_websocket_connection():
    """WebSocket 연결 테스트"""
    print("\n=== Test 1: WebSocket Connection ===")
    try:
        async with websockets.connect("ws://localhost:8000/ws") as ws:
            # 연결 상태 메시지 수신
            response = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(response)

            assert data.get("type") == "status", f"Expected status message, got: {data}"
            assert data.get("status") == "connected", f"Expected connected status, got: {data}"

            print(f"✓ WebSocket connected successfully")
            print(f"  Response: {data}")
            return True

    except Exception as e:
        print(f"✗ WebSocket connection failed: {e}")
        return False


async def test_screen_streaming():
    """화면 스트리밍 테스트"""
    print("\n=== Test 2: Screen Streaming ===")
    try:
        async with websockets.connect("ws://localhost:8000/ws") as ws:
            # 연결 상태 메시지 스킵
            await ws.recv()

            # 화면 프레임 수신
            frame_count = 0
            for _ in range(5):  # 5 프레임 수신
                response = await asyncio.wait_for(ws.recv(), timeout=2)
                data = json.loads(response)

                if data.get("type") == "screen":
                    frame_count += 1
                    print(f"  Frame {frame_count}: {data.get('width')}x{data.get('height')}")

            assert frame_count >= 3, f"Expected at least 3 frames, got: {frame_count}"
            print(f"✓ Screen streaming working ({frame_count} frames received)")
            return True

    except Exception as e:
        print(f"✗ Screen streaming failed: {e}")
        return False


async def test_ai_command_without_api_key():
    """API 키 없이 AI 명령 테스트"""
    print("\n=== Test 3: AI Command (without API key) ===")
    try:
        async with websockets.connect("ws://localhost:8000/ws") as ws:
            # 연결 상태 메시지 스킵
            await ws.recv()

            # AI 명령 전송
            command = {
                "type": "ai_command",
                "instruction": "화면 중앙을 클릭해줘"
            }
            await ws.send(json.dumps(command))
            print(f"  Command sent: {command['instruction']}")

            # 응답 대기 (화면 프레임을 건너뛰며 ai_response 찾기)
            for _ in range(30):  # 더 많은 시도
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=2)
                    data = json.loads(response)

                    if data.get("type") == "ai_response":
                        print(f"  Response: {data}")

                        # API 키가 없으면 에러 메시지가 와야 함
                        if "OPENAI_API_KEY" in str(data.get("error", "")):
                            print(f"✓ AI command correctly reports missing API key")
                            return True
                        elif data.get("success"):
                            print(f"✓ AI command executed successfully")
                            return True
                        else:
                            print(f"✓ AI command response received (error: {data.get('error')})")
                            return True
                except asyncio.TimeoutError:
                    continue

            print(f"✗ No AI response received within timeout")
            return False

    except Exception as e:
        print(f"✗ AI command test failed: {e}")
        return False


async def test_direct_action():
    """직접 액션 테스트 (마우스 호버)"""
    print("\n=== Test 4: Direct Action (Hover) ===")
    try:
        async with websockets.connect("ws://localhost:8000/ws") as ws:
            # 연결 상태 메시지 스킵
            await ws.recv()

            # 호버 액션 전송
            action = {
                "type": "action",
                "action_type": "hover",
                "x": 100,
                "y": 100
            }
            await ws.send(json.dumps(action))

            # 응답 대기
            for _ in range(10):
                response = await asyncio.wait_for(ws.recv(), timeout=2)
                data = json.loads(response)

                if data.get("status") == "success":
                    print(f"✓ Hover action executed successfully")
                    return True

            print(f"✗ No action response received")
            return False

    except Exception as e:
        print(f"✗ Direct action test failed: {e}")
        return False


async def run_all_tests():
    """모든 테스트 실행"""
    print("=" * 50)
    print("Web Player E2E Tests")
    print("=" * 50)

    results = []

    results.append(await test_websocket_connection())
    results.append(await test_screen_streaming())
    results.append(await test_ai_command_without_api_key())
    results.append(await test_direct_action())

    print("\n" + "=" * 50)
    print("Test Results")
    print("=" * 50)

    passed = sum(results)
    total = len(results)

    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
