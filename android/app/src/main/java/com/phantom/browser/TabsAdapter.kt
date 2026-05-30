package com.phantom.browser

import android.view.LayoutInflater
import android.view.ViewGroup
import android.webkit.WebView
import android.widget.ImageButton
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView

/** Lists open tabs in the bottom-sheet switcher. */
class TabsAdapter(
    private val tabs: List<WebView>,
    private val onSelect: (Int) -> Unit,
    private val onClose: (Int) -> Unit,
) : RecyclerView.Adapter<TabsAdapter.VH>() {

    class VH(v: android.view.View) : RecyclerView.ViewHolder(v) {
        val title: TextView = v.findViewById(R.id.tabTitle)
        val url: TextView = v.findViewById(R.id.tabUrl)
        val close: ImageButton = v.findViewById(R.id.tabClose)
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): VH {
        val v = LayoutInflater.from(parent.context).inflate(R.layout.item_tab, parent, false)
        return VH(v)
    }

    override fun onBindViewHolder(holder: VH, position: Int) {
        val wv = tabs[position]
        val t = wv.title?.takeIf { it.isNotBlank() } ?: "Новая вкладка"
        holder.title.text = t
        holder.url.text = MainActivity.prettyUrl(wv.url)
        holder.itemView.setOnClickListener { onSelect(holder.bindingAdapterPosition) }
        holder.close.setOnClickListener { onClose(holder.bindingAdapterPosition) }
    }

    override fun getItemCount(): Int = tabs.size
}
