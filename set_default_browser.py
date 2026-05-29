# -*- coding: utf-8 -*-
r"""
Регистрирует Phantom Browser как браузер в Windows (ветка HKCU — без прав админа)
и открывает «Приложения по умолчанию», где нужно ВРУЧНУЮ выбрать Phantom для
http/https. Windows 10/11 не даёт назначить браузер по умолчанию программно.

Запускать ПОСЛЕ сборки .exe (build_exe.bat):
    python set_default_browser.py
По умолчанию ищет dist\PhantomBrowser\PhantomBrowser.exe рядом со скриптом.
Можно указать путь явно:  python set_default_browser.py "C:\путь\PhantomBrowser.exe"
"""

import os
import sys
import winreg

APP_NAME = "Phantom"
PROG_ID = "PhantomHTML"


def find_exe() -> str:
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        return os.path.abspath(sys.argv[1])
    here = os.path.dirname(os.path.abspath(__file__))
    guess = os.path.join(here, "dist", "PhantomBrowser", "PhantomBrowser.exe")
    return guess


def set_value(root, path, name, value):
    with winreg.CreateKey(root, path) as k:
        winreg.SetValueEx(k, name, 0, winreg.REG_SZ, value)


def register(exe: str):
    hkcu = winreg.HKEY_CURRENT_USER
    cmd = f'"{exe}" "%1"'
    classes = r"Software\Classes"

    # ProgID и команда запуска
    set_value(hkcu, fr"{classes}\{PROG_ID}", "", "Phantom HTML Document")
    set_value(hkcu, fr"{classes}\{PROG_ID}\DefaultIcon", "", f"{exe},0")
    set_value(hkcu, fr"{classes}\{PROG_ID}\shell\open\command", "", cmd)

    # Capabilities — чтобы Phantom появился в списке браузеров
    caps = fr"Software\{APP_NAME}\Capabilities"
    set_value(hkcu, caps, "ApplicationName", "Phantom Browser")
    set_value(hkcu, caps, "ApplicationDescription", "Privacy-first AI browser on PyQt6")
    set_value(hkcu, fr"{caps}\StartMenu", "StartMenuInternet", APP_NAME)
    for scheme in ("http", "https"):
        set_value(hkcu, fr"{caps}\URLAssociations", scheme, PROG_ID)
    for ext in (".htm", ".html"):
        set_value(hkcu, fr"{caps}\FileAssociations", ext, PROG_ID)

    # Регистрируем приложение в системе
    set_value(hkcu, r"Software\RegisteredApplications", APP_NAME,
              fr"Software\{APP_NAME}\Capabilities")

    # StartMenuInternet — классическая регистрация браузера
    smi = fr"Software\Clients\StartMenuInternet\{APP_NAME}"
    set_value(hkcu, smi, "", "Phantom Browser")
    set_value(hkcu, fr"{smi}\DefaultIcon", "", f"{exe},0")
    set_value(hkcu, fr"{smi}\shell\open\command", "", f'"{exe}"')
    set_value(hkcu, fr"{smi}\Capabilities", "ApplicationName", "Phantom Browser")
    for scheme in ("http", "https"):
        set_value(hkcu, fr"{smi}\Capabilities\URLAssociations", scheme, PROG_ID)


def main():
    exe = find_exe()
    if not os.path.isfile(exe):
        print(f"[!] Не найден .exe: {exe}")
        print("    Сначала собери браузер: build_exe.bat")
        print("    Или укажи путь: python set_default_browser.py \"C:\\...\\PhantomBrowser.exe\"")
        return
    register(exe)
    print(f"[OK] Phantom зарегистрирован для exe:\n     {exe}")
    print("[->] Открываю «Приложения по умолчанию». Выбери Phantom для HTTP и HTTPS.")
    try:
        os.startfile("ms-settings:defaultapps")
    except Exception:
        pass


if __name__ == "__main__":
    main()
