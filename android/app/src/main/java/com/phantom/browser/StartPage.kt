package com.phantom.browser

/**
 * Builds the Phantom start page (the "phantom://home" screen) as a self-contained
 * HTML document — Catppuccin Mocha theme, big Phantom Search box, live clock and
 * quick-link tiles. Mirrors the desktop start page.
 */
object StartPage {

    fun html(): String = """
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<title>Phantom</title>
<style>
  :root{
    --base:#1e1e2e; --mantle:#181825; --crust:#11111b;
    --surface0:#313244; --surface1:#45475a; --overlay0:#6c7086;
    --text:#cdd6f4; --sub:#a6adc8; --mauve:#cba6f7; --lav:#b4befe;
    --blue:#89b4fa; --green:#a6e3a1; --peach:#fab387; --red:#f38ba8;
  }
  *{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
  html,body{margin:0;height:100%}
  body{
    font-family:-apple-system,Roboto,"Segoe UI",sans-serif;
    background:radial-gradient(1200px 800px at 50% -10%, #2a2a40 0%, var(--base) 55%, var(--mantle) 100%);
    color:var(--text);display:flex;flex-direction:column;align-items:center;
    justify-content:flex-start;padding:0 20px;min-height:100%;
  }
  .wrap{width:100%;max-width:560px;display:flex;flex-direction:column;align-items:center}
  .clock{margin-top:14vh;font-size:58px;font-weight:700;letter-spacing:2px;
    background:linear-gradient(120deg,var(--mauve),var(--lav),var(--blue));
    -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}
  .date{color:var(--sub);font-size:14px;margin-top:2px;text-transform:capitalize}
  .ghost{font-size:64px;margin-top:26px;filter:drop-shadow(0 8px 24px rgba(203,166,247,.35));
    animation:float 4s ease-in-out infinite}
  @keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-12px)}}
  .brand{font-size:26px;font-weight:800;letter-spacing:6px;margin-top:8px}
  .tag{color:var(--overlay0);font-size:12px;margin-top:2px}
  form{width:100%;margin-top:26px;position:relative}
  input{width:100%;border:1px solid var(--surface1);background:var(--surface0);
    color:var(--text);font-size:17px;padding:16px 54px 16px 22px;border-radius:30px;outline:none}
  input::placeholder{color:var(--overlay0)}
  input:focus{border-color:var(--mauve);box-shadow:0 0 0 4px rgba(203,166,247,.15)}
  .go{position:absolute;right:8px;top:50%;transform:translateY(-50%);
    width:42px;height:42px;border:none;border-radius:50%;cursor:pointer;
    background:linear-gradient(135deg,var(--mauve),var(--blue));color:var(--crust);
    font-size:20px;display:flex;align-items:center;justify-content:center}
  .tiles{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-top:34px;width:100%}
  .tile{background:var(--surface0);border:1px solid var(--surface1);border-radius:18px;
    padding:16px 6px;text-align:center;text-decoration:none;color:var(--text);
    transition:transform .12s ease,border-color .12s ease}
  .tile:active{transform:scale(.94)}
  .tile .ic{font-size:24px}
  .tile .lb{font-size:11px;color:var(--sub);margin-top:6px;display:block}
  .foot{margin:36px 0 22px;color:var(--overlay0);font-size:11px;text-align:center}
  .foot b{color:var(--mauve)}
</style>
</head>
<body>
  <div class="wrap">
    <div class="clock" id="clock">--:--</div>
    <div class="date" id="date"></div>
    <div class="ghost">👻</div>
    <div class="brand">PHANTOM</div>
    <div class="tag">Phantom Search · приватный поиск</div>

    <form onsubmit="return go(event)">
      <input id="q" autocomplete="off" autocapitalize="off" spellcheck="false"
             placeholder="Поиск в Phantom или ввод адреса">
      <button class="go" type="submit" aria-label="Искать">➜</button>
    </form>

    <div class="tiles">
      <a class="tile" href="https://www.youtube.com"><div class="ic">▶️</div><span class="lb">YouTube</span></a>
      <a class="tile" href="https://github.com"><div class="ic">🐙</div><span class="lb">GitHub</span></a>
      <a class="tile" href="https://ru.wikipedia.org"><div class="ic">📚</div><span class="lb">Wiki</span></a>
      <a class="tile" href="https://t.me"><div class="ic">✈️</div><span class="lb">Telegram</span></a>
      <a class="tile" href="https://maps.google.com"><div class="ic">🗺️</div><span class="lb">Карты</span></a>
      <a class="tile" href="https://mail.google.com"><div class="ic">✉️</div><span class="lb">Почта</span></a>
      <a class="tile" href="https://www.reddit.com"><div class="ic">👽</div><span class="lb">Reddit</span></a>
      <a class="tile" href="https://chat.openai.com"><div class="ic">✨</div><span class="lb">AI</span></a>
    </div>

    <div class="foot">👻 <b>Phantom Browser</b> для Android · убийца Chrome теперь в кармане</div>
  </div>

<script>
  var SEARCH = "${PhantomApp.SEARCH_QUERY_URL}";
  function go(e){
    e.preventDefault();
    var v=(document.getElementById('q').value||'').trim();
    if(!v) return false;
    if(v==='antigravity'){location.href='https://xkcd.com/353/';return false;}
    var isUrl=/^https?:\/\//i.test(v) || (/^[\w-]+(\.[\w-]+)+(\/.*)?$/.test(v) && v.indexOf(' ')<0);
    location.href = isUrl ? (/^https?:\/\//i.test(v)?v:'https://'+v) : SEARCH+encodeURIComponent(v);
    return false;
  }
  function tick(){
    var d=new Date();
    var hh=String(d.getHours()).padStart(2,'0'), mm=String(d.getMinutes()).padStart(2,'0');
    document.getElementById('clock').textContent=hh+':'+mm;
    document.getElementById('date').textContent=d.toLocaleDateString('ru-RU',
      {weekday:'long',day:'numeric',month:'long'});
  }
  tick(); setInterval(tick,1000);
</script>
</body>
</html>
""".trimIndent()
}
