package com.phantom.browser

import android.annotation.SuppressLint
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.Color
import android.net.Uri
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.webkit.CookieManager
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.FrameLayout
import android.widget.PopupMenu
import android.widget.TextView
import android.widget.Toast
import androidx.activity.OnBackPressedCallback
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.google.android.material.bottomsheet.BottomSheetDialog
import com.phantom.browser.databinding.ActivityMainBinding

class MainActivity : AppCompatActivity() {

    private lateinit var b: ActivityMainBinding

    private val tabs = mutableListOf<WebView>()
    private var current = -1

    private var ghostMode = false
    private var desktopMode = false

    private val currentTab: WebView? get() = tabs.getOrNull(current)

    companion object {
        private const val HOME_BASE = "https://phantom.local/"

        /** Friendly URL for display: hide the internal start-page base. */
        fun prettyUrl(url: String?): String {
            if (url.isNullOrBlank() || url.startsWith(HOME_BASE) ||
                url == "about:blank" || url.startsWith("data:")
            ) return "phantom://home"
            return url
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        b = ActivityMainBinding.inflate(layoutInflater)
        setContentView(b.root)

        wireToolbar()

        // Honour an inbound VIEW/SEND intent, otherwise open the start page.
        val incoming = intentUrl(intent)
        addTab(incoming ?: HOME_BASE)

        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() = handleBack()
        })
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        intentUrl(intent)?.let { addTab(it) }
    }

    private fun intentUrl(intent: Intent?): String? {
        if (intent == null) return null
        return when (intent.action) {
            Intent.ACTION_VIEW -> intent.dataString
            Intent.ACTION_SEND -> intent.getStringExtra(Intent.EXTRA_TEXT)
            else -> null
        }?.takeIf { it.isNotBlank() }
    }

    // ── Toolbar wiring ───────────────────────────────────────────────
    private fun wireToolbar() {
        b.omnibox.setOnEditorActionListener { _, _, _ ->
            navigate(b.omnibox.text.toString())
            b.omnibox.clearFocus()
            hideKeyboard()
            true
        }
        b.btnReload.setOnClickListener { currentTab?.let { if (loading) it.stopLoading() else it.reload() } }
        b.btnBack.setOnClickListener { currentTab?.takeIf { it.canGoBack() }?.goBack() }
        b.btnForward.setOnClickListener { currentTab?.takeIf { it.canGoForward() }?.goForward() }
        b.btnNewTab.setOnClickListener { addTab(HOME_BASE) }
        b.btnTabs.setOnClickListener { showTabs() }
        b.btnMenu.setOnClickListener { showMenu(it) }
    }

    private var loading = false

    private fun hideKeyboard() {
        val imm = getSystemService(INPUT_METHOD_SERVICE) as android.view.inputmethod.InputMethodManager
        imm.hideSoftInputFromWindow(b.omnibox.windowToken, 0)
    }

    // ── Navigation ───────────────────────────────────────────────────
    private fun navigate(raw: String) {
        val q = raw.trim()
        if (q.isEmpty()) return
        if (q == "antigravity") { currentTab?.loadUrl("https://xkcd.com/353/"); return }
        val url = when {
            q.matches(Regex("^https?://.*", RegexOption.IGNORE_CASE)) -> q
            looksLikeDomain(q) -> "https://$q"
            else -> PhantomApp.SEARCH_QUERY_URL + Uri.encode(q)
        }
        currentTab?.loadUrl(url)
    }

    private fun looksLikeDomain(s: String): Boolean =
        !s.contains(' ') && s.matches(Regex("^[\\w-]+(\\.[\\w-]+)+(/.*)?$"))

    // ── Tabs ─────────────────────────────────────────────────────────
    @SuppressLint("SetJavaScriptEnabled")
    private fun newWebView(): WebView {
        val wv = WebView(this)
        wv.layoutParams = FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.MATCH_PARENT
        )
        wv.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            useWideViewPort = true
            loadWithOverviewMode = true
            builtInZoomControls = true
            displayZoomControls = false
            setSupportZoom(true)
            javaScriptCanOpenWindowsAutomatically = false
            mediaPlaybackRequiresUserGesture = true
            cacheMode = if (ghostMode) WebSettings.LOAD_NO_CACHE else WebSettings.LOAD_DEFAULT
            if (desktopMode) userAgentString = PhantomApp.DESKTOP_UA
        }

        wv.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView, req: WebResourceRequest): Boolean {
                val u = req.url
                val scheme = u.scheme ?: return false
                if (scheme == "http" || scheme == "https" || scheme == "about" || scheme == "data") return false
                // External schemes (tel:, mailto:, intent:, market:, tg: …) → system apps.
                return try {
                    startActivity(Intent(Intent.ACTION_VIEW, u)); true
                } catch (e: Exception) { true }
            }

            override fun onPageStarted(view: WebView, url: String?, favicon: Bitmap?) {
                if (view === currentTab) {
                    loading = true
                    b.omnibox.setText(displayUrl(url))
                    b.progress.visibility = View.VISIBLE
                }
            }

            override fun onPageFinished(view: WebView, url: String?) {
                if (view === currentTab) {
                    loading = false
                    b.progress.visibility = View.GONE
                    b.omnibox.setText(displayUrl(url))
                }
            }
        }

        wv.webChromeClient = object : WebChromeClient() {
            override fun onProgressChanged(view: WebView, newProgress: Int) {
                if (view === currentTab) {
                    b.progress.progress = newProgress
                    b.progress.visibility = if (newProgress in 1..99) View.VISIBLE else View.GONE
                }
            }
        }
        return wv
    }

    private fun displayUrl(url: String?): String {
        if (url == null) return ""
        return if (url.startsWith(HOME_BASE) || url == "about:blank" || url.startsWith("data:")) ""
        else url
    }

    private fun addTab(target: String) {
        val wv = newWebView()
        tabs.add(wv)
        selectTab(tabs.size - 1)
        loadInto(wv, target)
        updateTabCount()
    }

    private fun loadInto(wv: WebView, target: String) {
        if (target == HOME_BASE || target == "phantom://home") {
            wv.loadDataWithBaseURL(HOME_BASE, StartPage.html(), "text/html", "utf-8", HOME_BASE)
        } else {
            wv.loadUrl(target)
        }
    }

    private fun selectTab(index: Int) {
        if (index < 0 || index >= tabs.size) return
        current = index
        b.webContainer.removeAllViews()
        b.webContainer.addView(tabs[index])
        val wv = tabs[index]
        b.omnibox.setText(displayUrl(wv.url))
        updateTabCount()
    }

    private fun closeTab(index: Int) {
        if (index !in tabs.indices) return
        val wv = tabs.removeAt(index)
        if (wv === b.webContainer.getChildAt(0)) b.webContainer.removeView(wv)
        wv.destroy()
        if (tabs.isEmpty()) { addTab(HOME_BASE); return }
        selectTab(index.coerceAtMost(tabs.size - 1))
    }

    private fun updateTabCount() { b.tabCount.text = tabs.size.toString() }

    // ── Tab switcher (bottom sheet) ──────────────────────────────────
    private fun showTabs() {
        val sheet = BottomSheetDialog(this)
        val view = layoutInflater.inflate(R.layout.sheet_tabs, null)
        val rv = view.findViewById<RecyclerView>(R.id.tabsRecycler)
        rv.layoutManager = LinearLayoutManager(this)
        rv.adapter = TabsAdapter(
            tabs,
            onSelect = { i -> selectTab(i); sheet.dismiss() },
            onClose = { i ->
                closeTab(i)
                if (tabs.isEmpty()) sheet.dismiss() else rv.adapter?.notifyDataSetChanged()
                updateTabCount()
            }
        )
        view.findViewById<TextView>(R.id.sheetNewTab).setOnClickListener {
            addTab(HOME_BASE); sheet.dismiss()
        }
        sheet.setContentView(view)
        sheet.show()
    }

    // ── Overflow menu ────────────────────────────────────────────────
    private fun showMenu(anchor: View) {
        val pm = PopupMenu(this, anchor, Gravity.END)
        pm.menuInflater.inflate(R.menu.main_menu, pm.menu)
        pm.menu.findItem(R.id.menu_ghost).isChecked = ghostMode
        pm.menu.findItem(R.id.menu_desktop).isChecked = desktopMode
        pm.setOnMenuItemClickListener { item ->
            when (item.itemId) {
                R.id.menu_new_tab -> addTab(HOME_BASE)
                R.id.menu_home -> currentTab?.let { loadInto(it, HOME_BASE) }
                R.id.menu_share -> shareCurrent()
                R.id.menu_ghost -> toggleGhost()
                R.id.menu_desktop -> toggleDesktop()
                R.id.menu_about -> showAbout()
            }
            true
        }
        pm.show()
    }

    private fun shareCurrent() {
        val url = currentTab?.url ?: return
        if (url.startsWith(HOME_BASE)) return
        val send = Intent(Intent.ACTION_SEND).apply {
            type = "text/plain"
            putExtra(Intent.EXTRA_TEXT, url)
            putExtra(Intent.EXTRA_SUBJECT, currentTab?.title ?: "Phantom")
        }
        startActivity(Intent.createChooser(send, getString(R.string.action_share)))
    }

    private fun toggleGhost() {
        ghostMode = !ghostMode
        if (ghostMode) {
            CookieManager.getInstance().removeAllCookies(null)
            window.statusBarColor = Color.parseColor("#6C2BD9")
        } else {
            window.statusBarColor = Color.parseColor("#11111B")
        }
        // Apply cache policy to all live tabs.
        tabs.forEach {
            it.settings.cacheMode = if (ghostMode) WebSettings.LOAD_NO_CACHE else WebSettings.LOAD_DEFAULT
        }
        b.ghostBadge.alpha = if (ghostMode) 0.55f else 1f
        Toast.makeText(this, if (ghostMode) R.string.ghost_on else R.string.ghost_off, Toast.LENGTH_SHORT).show()
    }

    private fun toggleDesktop() {
        desktopMode = !desktopMode
        tabs.forEach { it.settings.userAgentString = if (desktopMode) PhantomApp.DESKTOP_UA else null }
        currentTab?.reload()
        Toast.makeText(this, if (desktopMode) "Версия для ПК" else "Мобильная версия", Toast.LENGTH_SHORT).show()
    }

    private fun showAbout() {
        AlertDialog.Builder(this)
            .setTitle("👻 Phantom Browser")
            .setMessage(
                "Phantom Browser v3.0 — Android edition.\n\n" +
                    "Лёгкий приватный браузер с собственной поисковой системой " +
                    "«Phantom Search», вкладками, Ghost Mode и тёмной темой Catppuccin.\n\n" +
                    "Десктоп-версия: Python + PyQt6.\n" +
                    "github.com/NikMusy/PhantomBrowser"
            )
            .setPositiveButton("OK", null)
            .show()
    }

    // ── Back handling ────────────────────────────────────────────────
    private fun handleBack() {
        val wv = currentTab
        when {
            wv != null && wv.canGoBack() -> wv.goBack()
            tabs.size > 1 -> closeTab(current)
            else -> finish()
        }
    }

    override fun onDestroy() {
        tabs.forEach { it.destroy() }
        tabs.clear()
        super.onDestroy()
    }
}
