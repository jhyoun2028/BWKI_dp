package de.doppelcheck.app.scan

import android.view.accessibility.AccessibilityNodeInfo

/** Turns an accessibility node tree into the plain text a user currently sees. */
object ScreenTextCollector {

    /** Guard against pathological trees (endless lists); a normal screen has a few hundred nodes. */
    private const val MAX_NODES = 5000

    /**
     * Depth-first (pre-order) walk from [root]. Collects `text` and `contentDescription` of every
     * node visible to the user, trimmed, without duplicates, in on-screen order, joined by newlines.
     * Subtrees of invisible nodes are skipped.
     */
    fun collect(root: AccessibilityNodeInfo): String {
        val lines = LinkedHashSet<String>()
        val stack = ArrayDeque<AccessibilityNodeInfo>()
        stack.addLast(root)
        var visited = 0
        while (stack.isNotEmpty() && visited < MAX_NODES) {
            val node = stack.removeLast()
            visited++
            if (!node.isVisibleToUser) continue
            addLine(lines, node.text)
            addLine(lines, node.contentDescription)
            // Push children in reverse so that child 0 is taken off the stack first.
            for (i in node.childCount - 1 downTo 0) {
                node.getChild(i)?.let(stack::addLast)
            }
        }
        return lines.joinToString("\n")
    }

    private fun addLine(lines: MutableSet<String>, value: CharSequence?) {
        val line = value?.toString()?.trim().orEmpty()
        if (line.isNotEmpty()) lines.add(line)
    }
}
