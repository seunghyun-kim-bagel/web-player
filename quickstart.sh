#!/bin/bash

# Web Player Quickstart Script
# 빠른 설정 및 실행을 위한 대화형 스크립트

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 프로젝트 루트 디렉토리
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$PROJECT_DIR/.env"
TOOLS_DIR="$PROJECT_DIR/tools"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Web Player Quickstart Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# .env 파일 존재 확인
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}⚠️  .env 파일이 없습니다. .env.example을 복사합니다.${NC}"
    cp "$PROJECT_DIR/.env.example" "$ENV_FILE"
fi

# 헬퍼 함수: .env 파일에 값 설정
update_env() {
    local key=$1
    local value=$2

    # 키가 이미 존재하면 업데이트, 없으면 추가
    if grep -q "^${key}=" "$ENV_FILE" 2>/dev/null; then
        # macOS/BSD sed와 GNU sed 모두 호환
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s|^${key}=.*|${key}=${value}|" "$ENV_FILE"
        else
            sed -i "s|^${key}=.*|${key}=${value}|" "$ENV_FILE"
        fi
    else
        echo "${key}=${value}" >> "$ENV_FILE"
    fi
}

# 단계 0: 실행 모드 선택
echo -e "${GREEN}단계 0: 실행 모드 선택${NC}"
echo "1) Desktop 모드 (화면 영역 지정)"
echo "2) Appium 모드 (모바일 제어)"
echo ""
read -p "선택 (1 또는 2): " mode_choice

case $mode_choice in
    1)
        MODE="desktop"
        echo -e "${GREEN}✓ Desktop 모드 선택${NC}"
        update_env "CONTROL_MODE" "desktop"
        ;;
    2)
        MODE="appium"
        echo -e "${GREEN}✓ Appium 모드 선택${NC}"
        update_env "CONTROL_MODE" "appium"
        ;;
    *)
        echo -e "${RED}❌ 잘못된 선택입니다. 종료합니다.${NC}"
        exit 1
        ;;
esac

echo ""

# 단계 1: 화면 영역 지정 (Desktop 모드만)
if [ "$MODE" == "desktop" ]; then
    echo -e "${GREEN}단계 1: 화면 영역 지정${NC}"
    echo -e "${YELLOW}화면에서 캡처할 영역을 선택하세요.${NC}"
    echo ""
    echo "사용 방법:"
    echo "  1. 전체 화면이 나타나면 마우스를 드래그하여 영역 선택"
    echo "  2. 영역 선택이 완료되면 마우스 버튼을 놓으세요"
    echo "  3. ESC 키를 누르면 취소됩니다"
    echo ""
    read -p "준비되셨으면 Enter를 눌러주세요..."

    # Python 가상환경 활성화 확인
    if [ -d "$PROJECT_DIR/venv" ]; then
        source "$PROJECT_DIR/venv/bin/activate"
    fi

    # region_selector.py 실행
    if [ -f "$TOOLS_DIR/region_selector.py" ]; then
        echo -e "${BLUE}영역 선택 툴을 실행합니다...${NC}"

        # Python 스크립트 실행 및 출력 캡처
        REGION_OUTPUT=$(python3 "$TOOLS_DIR/region_selector.py" 2>&1)
        REGION_EXIT_CODE=$?

        if [ $REGION_EXIT_CODE -eq 0 ]; then
            # 출력에서 REGION_* 값 추출하여 .env에 저장
            echo "$REGION_OUTPUT" | grep "^REGION_" | while read -r line; do
                key=$(echo "$line" | cut -d'=' -f1)
                value=$(echo "$line" | cut -d'=' -f2)
                update_env "$key" "$value"
            done

            echo -e "${GREEN}✓ 화면 영역이 설정되었습니다${NC}"
            echo "$REGION_OUTPUT" | grep "^REGION_"
        else
            echo -e "${RED}❌ 영역 선택이 취소되었습니다${NC}"
            exit 1
        fi
    else
        echo -e "${RED}❌ region_selector.py를 찾을 수 없습니다${NC}"
        exit 1
    fi
    echo ""
fi

# 단계 2: Goal Automation 설정
echo -e "${GREEN}단계 2: 목표 자동화 설정${NC}"
echo ""

read -p "최대 실행 스텝 (기본값: 50): " max_steps
max_steps=${max_steps:-50}
update_env "GOAL_MAX_STEPS" "$max_steps"
echo -e "${GREEN}✓ 최대 스텝: $max_steps${NC}"
echo ""

read -p "달성할 목표를 입력하세요 (예: 로그인 완료): " goal
if [ -z "$goal" ]; then
    echo -e "${YELLOW}⚠️  목표가 입력되지 않았습니다. 기본 실행 모드로 시작합니다.${NC}"
    update_env "GOAL_ENABLED" "false"
    update_env "GOAL_TEXT" ""
else
    update_env "GOAL_ENABLED" "true"
    update_env "GOAL_TEXT" "$goal"
    echo -e "${GREEN}✓ 목표: $goal${NC}"
fi
echo ""

# 단계 3: 실행
echo -e "${GREEN}단계 3: 프로그램 실행${NC}"
echo ""
echo -e "${BLUE}설정이 완료되었습니다. 서버를 시작합니다...${NC}"
echo ""
echo -e "${YELLOW}설정 요약:${NC}"
echo "  - 실행 모드: $MODE"
if [ "$MODE" == "desktop" ]; then
    echo "  - 화면 영역: $(grep REGION_X $ENV_FILE 2>/dev/null || echo '전체 화면')"
fi
echo "  - 최대 스텝: $max_steps"
if [ ! -z "$goal" ]; then
    echo "  - 목표: $goal"
fi
echo ""
echo -e "${BLUE}브라우저에서 http://localhost:8000 접속하세요${NC}"
echo ""

# 가상환경이 있으면 활성화
if [ -d "$PROJECT_DIR/venv" ]; then
    source "$PROJECT_DIR/venv/bin/activate"
fi

# 서버 실행
cd "$PROJECT_DIR"
python run.py
