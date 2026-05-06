"""词途 · AI 英语单词学习闯关系统（覆盖小学/初中/高中）— 主程序入口"""
from app_gui import YingyuApp
import voice

if __name__ == "__main__":
    voice.prewarm()
    app = YingyuApp()
    app.mainloop()
