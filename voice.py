"""voice.py — 英语单词发音（Windows 自带 System.Speech，零外部依赖）

设计：维护一个长期运行的 PowerShell 后台进程，通过 stdin 写入命令；
PowerShell 端 SpeakAsync 异步播放，新发音会先 SpeakAsyncCancelAll() 抢占旧的。
首次发音前 PowerShell 进程已就绪，单次发音延迟 < 50ms。

外部接口：
    from voice import speak, prewarm, shutdown
    prewarm()        # 应用启动时调用一次（可选；首次 speak 会自动启）
    speak("hello")   # 后台异步发音，立即返回
    shutdown()       # 应用退出前调用（atexit 已注册）

失败兏底：当前不在 Windows、找不到 powershell.exe、或子进程崩溃时，
speak() 会静默失败（不抛异常、不弹窗），保证 UI 不会因为发音问题崩溃。
"""
from __future__ import annotations

import atexit
import os
import subprocess
import sys
import threading

# Windows: 不弹出黑色 console 窗口
_CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0

# PowerShell 端：加载 SpeechSynthesizer，循环读 stdin，每行一句要朗读的文本。
# 'STOP' 会立即停止当前发音；其他文本会先取消、再 SpeakAsync。
_PS_LOOP = r"""
$ErrorActionPreference = 'SilentlyContinue'
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.Rate = 0
$s.Volume = 100
foreach ($v in $s.GetInstalledVoices()) {
    if ($v.VoiceInfo.Culture.Name -like 'en-*') { $s.SelectVoice($v.VoiceInfo.Name); break }
}
while ($true) {
    $line = [Console]::In.ReadLine()
    if ($null -eq $line) { break }
    if ($line -eq 'STOP') {
        $s.SpeakAsyncCancelAll()
    } elseif ($line.Length -gt 0) {
        $s.SpeakAsyncCancelAll()
        $null = $s.SpeakAsync($line)
    }
}
$s.Dispose()
"""


class _Voice:
    def __init__(self):
        self._proc: subprocess.Popen | None = None
        self._lock = threading.Lock()
        self._broken = False  # 启动失败后停止再尝试，避免每次 speak 都炸

    def _ensure_proc(self) -> bool:
        if self._broken:
            return False
        if self._proc is not None and self._proc.poll() is None:
            return True
        if os.name != "nt":
            self._broken = True
            return False
        try:
            self._proc = subprocess.Popen(
                ["powershell.exe", "-NoProfile", "-NonInteractive",
                 "-ExecutionPolicy", "Bypass", "-Command", _PS_LOOP],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=_CREATE_NO_WINDOW,
            )
        except (FileNotFoundError, OSError):
            self._broken = True
            self._proc = None
            return False
        return True

    def speak(self, text: str):
        text = (text or "").strip()
        if not text:
            return
        # 仅保留单行：PowerShell 后端按行解析
        text = text.replace("\r", " ").replace("\n", " ")
        with self._lock:
            if not self._ensure_proc():
                return
            try:
                assert self._proc and self._proc.stdin
                self._proc.stdin.write((text + "\n").encode("utf-8"))
                self._proc.stdin.flush()
            except (BrokenPipeError, OSError, ValueError):
                # 子进程崩溃，下次 speak 时尝试重启
                try:
                    if self._proc:
                        self._proc.kill()
                except Exception:
                    pass
                self._proc = None

    def stop(self):
        with self._lock:
            if self._proc and self._proc.poll() is None and self._proc.stdin:
                try:
                    self._proc.stdin.write(b"STOP\n")
                    self._proc.stdin.flush()
                except Exception:
                    pass

    def shutdown(self):
        with self._lock:
            if self._proc:
                try:
                    if self._proc.stdin:
                        self._proc.stdin.close()
                except Exception:
                    pass
                try:
                    self._proc.terminate()
                except Exception:
                    pass
                self._proc = None


_singleton = _Voice()


def prewarm():
    """应用启动时调用一次（可选）：提前 spawn PowerShell 后端，减少首次发音延迟。"""
    threading.Thread(target=_singleton._ensure_proc, daemon=True).start()


def speak(text: str):
    """后台异步朗读，立即返回。多次调用会抢占式播放最新文本。"""
    _singleton.speak(text)


def stop():
    """立即停止当前发音。"""
    _singleton.stop()


def shutdown():
    """关闭后台 PowerShell 进程。已注册到 atexit。"""
    _singleton.shutdown()


atexit.register(shutdown)
