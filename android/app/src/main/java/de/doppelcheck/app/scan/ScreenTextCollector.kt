package de.doppelcheck.app.scan

import android.view.accessibility.AccessibilityNodeInfo

/** Turns an accessibility node tree into the plain text a user currently sees. */
object ScreenTextCollector {

    /** Guard against pathological trees (endless lists); a normal screen has a few hundred nodes. */
    private const val MAX_NODES = 5000

    /** One collected string plus the node it came from (for the debug dump and later filters). */
    data class Entry(
        val text: String,
        val className: String?,
        val viewId: String?,
        val depth: Int,
        val clickable: Boolean,
        /** true if [text] is the node's contentDescription, false if it is the node's text. */
        val fromDescription: Boolean,
    )

    /**
     * Depth-first (pre-order) walk from [root]. Collects `text` and `contentDescription` of every
     * node visible to the user, trimmed, without duplicates, in on-screen order.
     * Subtrees of invisible nodes are skipped.
     */
    fun collectEntries(root: AccessibilityNodeInfo): List<Entry> {
        val entries = mutableListOf<Entry>()
        val seen = HashSet<String>()
        val stack = ArrayDeque<Pair<AccessibilityNodeInfo, Int>>()
        stack.addLast(root to 0)
        var visited = 0
        while (stack.isNotEmpty() && visited < MAX_NODES) {
            val (node, depth) = stack.removeLast()
            visited++
            if (!node.isVisibleToUser) continue
            addEntry(entries, seen, node, depth, node.text, fromDescription = false)
            addEntry(entries, seen, node, depth, node.contentDescription, fromDescription = true)
            // Push children in reverse so that child 0 is taken off the stack first.
            for (i in node.childCount - 1 downTo 0) {
                node.getChild(i)?.let { stack.addLast(it to depth + 1) }
            }
        }
        return entries
    }

    /** The text sent to the server: all entries joined by newlines. */
    fun joinText(entries: List<Entry>): String = entries.joinToString("\n") { it.text }

    private fun addEntry(
        entries: MutableList<Entry>,
        seen: MutableSet<String>,
        node: AccessibilityNodeInfo,
        depth: Int,
        value: CharSequence?,
        fromDescription: Boolean,
    ) {
        val line = value?.toString()?.trim().orEmpty()
        if (line.isEmpty() || !seen.add(line)) return
        entries += Entry(
            text = line,
            className = node.className?.toString(),
            viewId = node.viewIdResourceName,
            depth = depth,
            clickable = node.isClickable,
            fromDescription = fromDescription,
        )
    }
}
