# 👻 Phantom Browser v3 — убийца Chrome и Comet

Премиальный браузер на **Python + PyQt6 + QtWebEngine** со **стилистикой Chrome**:
вкладки прямо в заголовке окна, тёмная тема Catppuccin, своя поисковая система,
AI-ассистент (как в Comet), режим анонимности через Tor и пасхалка 🚀 Antigravity.

## ⬇️ Скачать

**[Скачать установщик → PhantomBrowserSetup.exe](https://github.com/NikMusy/PhantomBrowser/releases/latest)**
— один файл, ставится в пользовательскую папку **без прав администратора, как Chrome**.

---

## ✨ Что нового в v3

- **Вкладки в заголовке окна, как в Chrome.** Реализовано через кастомный Win32-каркас
  (`WM_NCCALCSIZE` / `WM_NCHITTEST`), поэтому при кастомном виде сохранены **нативные
  Aero Snap, изменение размера, тень и анимации** сворачивания/разворачивания.
  Кнопки окна нарисованы шрифтом Segoe Fluent Icons — выглядят как системные.
- **Своя поисковая система «Phantom Search».** Дефолтный поиск из адресной строки и
  большой поиск на стартовой странице. Бэкенд — приватный (DuckDuckGo), меняется одной
  строкой `SEARCH_QUERY_URL` в `main.py`.

---

## 📱 Phantom для Android (APK)

Теперь Phantom есть и на телефоне — нативное Android-приложение на **Kotlin + WebView**
с той же стилистикой: тёмная тема Catppuccin, своя поисковая система **Phantom Search**,
вкладки, **Ghost Mode** (инкогнито), анимированный сплэш с логотипом-призраком и красивая
стартовая страница с часами и плитками-ссылками.

Исходники — в папке [`android/`](android/).

### ⬇️ Скачать APK
APK собирается автоматически в **GitHub Actions** (workflow «Build Phantom APK»):
- При каждом пуше в `android/**` — артефакт **`PhantomBrowser-apk`** на вкладке
  *Actions → последний прогон → Artifacts*.
- При создании релиза APK прикрепляется к нему как `PhantomBrowser.apk`.

### 🔨 Собрать APK самому
```bash
cd android
./gradlew assembleDebug          # результат: app/build/outputs/apk/debug/app-debug.apk
```
Нужны JDK 17 и Android SDK (Android Studio подтянет всё сам — просто открой папку `android/`).

### ✨ Что внутри Android-версии
- **Phantom Search** — поиск из омнибокса и со стартовой страницы (бэкенд DuckDuckGo,
  меняется одной строкой `SEARCH_QUERY_URL` в `android/.../PhantomApp.kt`).
- **Вкладки** — нижняя панель + bottom-sheet переключатель вкладок.
- **Ghost Mode** 🌙 — режим инкогнито: чистит куки, не пишет кэш, подсвечивает статус-бар.
- **Версия для ПК** — переключение мобильного/десктопного User-Agent.
- **Открытие ссылок** — Phantom можно выбрать браузером по умолчанию и «Поделиться → Phantom».
- Пасхалка 🚀 `antigravity` работает и тут.

---

## 🚀 Запуск из исходников (десктоп)

```powershell
pip install -r requirements.txt
python main.py            # или двойной клик по run.bat
```

## 📦 Сборка в .exe

`build_exe.bat` или вручную:

```powershell
pyinstaller --noconfirm --windowed --name PhantomBrowser --collect-all PyQt6 main.py
```
Результат: `dist\PhantomBrowser\PhantomBrowser.exe`. На рабочем столе — ярлык.

## 📥 Установщик (как у Chrome)

После сборки `.exe` собери инсталлятор (нужен Inno Setup 6):

```powershell
.\build_installer.bat          # или: ISCC.exe installer.iss
```
Получишь `installer_out\PhantomBrowserSetup.exe` — один файл, который ставит браузер
**в пользовательскую папку без прав администратора (как Chrome)**: мастер установки,
ярлыки в меню Пуск и на рабочем столе, регистрация браузера (галочка) и деинсталлятор.

### Веб-загрузчик (стаб «как у Chrome»)
`web_installer.py` — крошечный загрузчик: качает `PhantomBrowserSetup.exe` с твоей
ссылки и запускает. Залей setup в интернет (GitHub Releases / прямая ссылка), впиши URL
в `DOWNLOAD_URL` и собери стаб:
```powershell
pyinstaller --onefile --windowed --name PhantomWebInstaller web_installer.py
```

## 🎬 Анимация запуска (как у Comet)

При старте проигрывается сплэш-экран: градиентный логотип PHANTOM, спиннер-дуга и
прогресс-бар, плавное появление/исчезание — затем открывается окно браузера.

---

## ✨ AI-ассистент (замена Comet)

Кнопка **✨ AI** открывает боковую панель: «📄 Резюме страницы» и чат по её содержимому.
Нужен ключ Anthropic (модель `claude-sonnet-4-6`):
```powershell
setx ANTHROPIC_API_KEY "sk-ant-..."
```

## 🧅 Ghost Mode (Tor)

Запусти Tor (Tor Browser → порт 9150, демон `tor` → 9050), жми **🌙 Ghost Mode**.
Включает SOCKS5 + спуфинг User-Agent Tor Browser + Off-The-Record профиль
(история/куки/сессия на диск не пишутся).

## 🌐 Браузер по умолчанию (замена Chrome)

После сборки `.exe`:
```powershell
python set_default_browser.py
```
Регистрирует Phantom в реестре (HKCU) и открывает настройки Windows — выбери Phantom
для HTTP/HTTPS (Win11 иначе не разрешает, только вручную).

---

## ⌨️ Горячие клавиши

| Клавиши | Действие | Клавиши | Действие |
|---|---|---|---|
| `Ctrl+T` | Новая вкладка | `Ctrl+F` | Поиск на странице |
| `Ctrl+W` | Закрыть вкладку | `Ctrl+D` | В закладки |
| `Ctrl+L` | Адресная строка | `Ctrl+Shift+B` | Панель закладок |
| `Ctrl+R`/`F5` | Обновить | `Ctrl+H` | История |
| `Alt+←`/`Alt+→` | Назад/Вперёд | `Ctrl+J` | Папка загрузок |
| `Ctrl + =/-/0` | Зум +/−/сброс | `F11` | Полный экран |

Бонус: введи `antigravity` в адресной строке 🚀

---

## 🗂️ Данные

`%APPDATA%\PhantomBrowser\` — `bookmarks.json`, `history.json`, `session.json`
(в Ghost-режиме история и сессия не сохраняются).

## ⚠️ Честные оговорки

- **Анонимность ≠ магия.** SOCKS5 через Tor работает, но против серьёзной угрозы
  (DNS/WebRTC) это демонстрация, а не замена настоящего Tor Browser.
- **Phantom Search** использует приватный бэкенд (DuckDuckGo) под своим брендом — это не
  собственный поисковый индекс, а кастомный фронт. Меняется одной строкой в `main.py`.
- **Кастомный заголовок** использует Win32-API и работает только на Windows. На других ОС
  браузер автоматически откатывается на нативный системный заголовок.
