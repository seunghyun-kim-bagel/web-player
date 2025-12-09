#!/usr/bin/env python3
"""
화면 영역 선택 툴
사용자가 마우스로 드래그하여 화면 영역을 선택하면 좌표를 출력합니다.
"""
import sys
import tkinter as tk
from tkinter import messagebox
from PIL import ImageGrab
import platform


class RegionSelector:
    def __init__(self):
        self.root = tk.Tk()
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-alpha', 0.3)
        self.root.configure(bg='black')

        # 상단에 안내 문구
        self.label = tk.Label(
            self.root,
            text="마우스를 드래그하여 캡처할 영역을 선택하세요 (ESC: 취소)",
            font=("Arial", 16),
            bg="yellow",
            fg="black"
        )
        self.label.pack(pady=20)

        self.canvas = tk.Canvas(
            self.root,
            cursor="cross",
            bg='black',
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.start_x = None
        self.start_y = None
        self.rect = None
        self.result = None

        # 이벤트 바인딩
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.root.bind("<Escape>", lambda e: self.cancel())

    def on_press(self, event):
        """마우스 버튼 누름"""
        self.start_x = event.x
        self.start_y = event.y

        if self.rect:
            self.canvas.delete(self.rect)

        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline='red', width=3
        )

    def on_drag(self, event):
        """마우스 드래그"""
        if self.rect:
            self.canvas.coords(
                self.rect,
                self.start_x, self.start_y, event.x, event.y
            )

    def on_release(self, event):
        """마우스 버튼 릴리즈"""
        end_x = event.x
        end_y = event.y

        # 좌상단, 우하단 좌표 계산
        x1 = min(self.start_x, end_x)
        y1 = min(self.start_y, end_y)
        x2 = max(self.start_x, end_x)
        y2 = max(self.start_y, end_y)

        width = x2 - x1
        height = y2 - y1

        # 최소 크기 체크
        if width < 50 or height < 50:
            messagebox.showwarning("경고", "선택 영역이 너무 작습니다 (최소 50x50)")
            return

        # 결과 저장
        self.result = {
            'x': x1,
            'y': y1,
            'width': width,
            'height': height
        }

        self.root.quit()

    def cancel(self):
        """취소"""
        self.result = None
        self.root.quit()

    def run(self):
        """실행"""
        self.root.mainloop()
        self.root.destroy()
        return self.result


def main():
    """메인 함수"""
    print("화면 영역 선택 툴을 시작합니다...")
    print("마우스로 드래그하여 캡처할 영역을 선택하세요.")
    print("ESC를 누르면 취소됩니다.\n")

    selector = RegionSelector()
    result = selector.run()

    if result:
        print(f"REGION_X={result['x']}")
        print(f"REGION_Y={result['y']}")
        print(f"REGION_WIDTH={result['width']}")
        print(f"REGION_HEIGHT={result['height']}")
        return 0
    else:
        print("취소되었습니다.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
