# -*- coding: utf-8 -*-
r"""
Phantom Web Installer — мини-загрузчик в стиле Google Chrome.
Маленький .exe: скачивает PhantomBrowserSetup.exe с заданного URL и запускает его.

КАК ИСПОЛЬЗОВАТЬ:
  1) Собери установщик (build_installer.bat) → installer_out\PhantomBrowserSetup.exe
  2) Залей этот файл в интернет (GitHub Releases / прямая ссылка на файл).
  3) Впиши ссылку в DOWNLOAD_URL ниже.
  4) Собери крошечный загрузчик (tkinter — стдлиб, поэтому .exe лёгкий):
        pyinstaller --onefile --windowed --name PhantomWebInstaller web_installer.py
  Готово: PhantomWebInstaller.exe скачивает и ставит браузер, как стаб Chrome.
"""

import os
import sys
import tempfile
import threading
import subprocess
import urllib.request
import tkinter as tk
from tkinter import ttk

DOWNLOAD_URL = "https://github.com/NikMusy/PhantomBrowser/releases/download/v3.0/PhantomBrowserSetup.exe"


class Installer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Phantom Browser")
        self.root.configure(bg="#1E1E2E")
        self.root.resizable(False, False)
        w, h = 460, 200
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw - w)//2}+{(sh - h)//2}")

        tk.Label(self.root, text="◆ PHANTOM", fg="#89B4FA", bg="#1E1E2E",
                 font=("Segoe UI", 26, "bold")).pack(pady=(26, 2))
        tk.Label(self.root, text="Загрузка браузера…", fg="#A6ADC8", bg="#1E1E2E",
                 font=("Segoe UI", 10)).pack()

        style = ttk.Style(self.root)
        try:
            style.theme_use("default")
            style.configure("P.Horizontal.TProgressbar", troughcolor="#313244",
                            background="#89B4FA", bordercolor="#1E1E2E",
                            lightcolor="#89B4FA", darkcolor="#89B4FA")
        except Exception:
            pass
        self.bar = ttk.Progressbar(self.root, style="P.Horizontal.TProgressbar",
                                   length=380, mode="determinate", maximum=100)
        self.bar.pack(pady=18)
        self.status = tk.Label(self.root, text="", fg="#6C7086", bg="#1E1E2E",
                               font=("Segoe UI", 9))
        self.status.pack()

        self.root.after(400, lambda: threading.Thread(target=self._download, daemon=True).start())

    def _ui(self, fn):
        self.root.after(0, fn)

    def _set(self, pct, text):
        def upd():
            self.bar["value"] = pct
            self.status.configure(text=text)
        self._ui(upd)

    def _download(self):
        try:
            dst = os.path.join(tempfile.gettempdir(), "PhantomBrowserSetup.exe")
            req = urllib.request.Request(DOWNLOAD_URL, headers={"User-Agent": "PhantomWebInstaller"})
            with urllib.request.urlopen(req, timeout=60) as r:
                total = int(r.headers.get("Content-Length", 0))
                got = 0
                with open(dst, "wb") as f:
                    while True:
                        chunk = r.read(131072)
                        if not chunk:
                            break
                        f.write(chunk)
                        got += len(chunk)
                        if total:
                            self._set(got * 100 // total,
                                      f"{got // 1048576} / {total // 1048576} МБ")
                        else:
                            self._set(0, f"{got // 1048576} МБ")
            self._ui(lambda: self._launch(dst))
        except Exception as e:
            self._ui(lambda: self._error(str(e)))

    def _launch(self, path):
        self.status.configure(text="Запуск установщика…")
        try:
            subprocess.Popen([path])
        except Exception as e:
            self._error(str(e))
            return
        self.root.after(700, self.root.destroy)

    def _error(self, msg):
        self.bar["value"] = 0
        self.status.configure(text="Ошибка: " + msg[:60], fg="#F38BA8")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    Installer().run()
