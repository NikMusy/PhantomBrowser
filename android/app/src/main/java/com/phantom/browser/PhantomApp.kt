package com.phantom.browser

import android.app.Application

/**
 * Phantom Browser — Android edition.
 *
 * A WebView-based browser that mirrors the look & feel of the desktop
 * Phantom Browser (PyQt6): Catppuccin Mocha dark theme, "Phantom Search",
 * tabbed browsing, a custom start page and a Ghost (incognito) mode.
 */
class PhantomApp : Application() {

    companion object {
        /** Default search backend for "Phantom Search" — private (DuckDuckGo),
         *  exactly like SEARCH_QUERY_URL in the desktop main.py. Change in one place. */
        const val SEARCH_QUERY_URL = "https://duckduckgo.com/?q="

        /** Internal scheme used by the start page. */
        const val HOME_URL = "about:blank#phantom-home"

        /** Desktop User-Agent used when "Desktop site" is enabled. */
        const val DESKTOP_UA =
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +
                "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 PhantomBrowser/3.0"
    }
}
