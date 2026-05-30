# Keep JS interface members callable from the Phantom start page.
-keepclassmembers class com.phantom.browser.** {
    @android.webkit.JavascriptInterface <methods>;
}
