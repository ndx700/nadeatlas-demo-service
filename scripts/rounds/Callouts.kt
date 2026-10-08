// Vendored verbatim from the app (app/src/main/java/com/ali/cs2utility/replay/Callouts.kt): the place names the replay
// screens use. Mirage's boxes come from places/de_mirage.json (the app's assets/maps/mirage/places.json).
package com.ali.cs2utility.replay

/**
 * Names for places on the current map, to say where a grenade was thrown from and where it came down.
 * Dust II uses the hand-placed list below: a position gets the name of the nearest spot, so names are
 * approximate near the border between two places. Other maps use the places the map itself defines
 * (tools/build_places.py): the smallest box around the position, else the nearest box.
 * Coordinates are display metres (x, z).
 */
object Callouts {
    private class Spot(val name: String, val x: Float, val z: Float)
    private val spots = listOf(
        Spot("匪家", -20.3f, 20.3f), Spot("匪家", -11.5f, 16.8f), Spot("匪家", 4f, 17f), Spot("匪家", -8f, 29f), Spot("匪家斜坡", -12.3f, 6f), Spot("A外", 8.9f, -2.3f), Spot("A大门", 22.4f, -26.6f), Spot("A大", 35.6f, -33.0f),
        Spot("A大", 40.5f, -29.2f), Spot("蓝车", 44.7f, -51.0f), Spot("A大过点", 30.3f, -56.0f), Spot("A包点", 27.0f, -59.1f), Spot("A平台", 27.9f, -64.8f),
        Spot("A小", 6.3f, -44.5f), Spot("中路", -9.8f, -28.9f), Spot("Xbox", -7.0f, -34.2f), Spot("中门", -12.0f, -41.7f),
        Spot("警家中路", -4.7f, -56.5f), Spot("警家中路", -14.4f, -54.6f), Spot("警家", 4.0f, -62.5f), Spot("警家", -13.8f, -62.3f),
        Spot("B1", -22.1f, -35.8f), Spot("B2", -43.2f, -27.9f), Spot("后花园", -33.5f, 10.5f), Spot("后花园", -36.5f, 4.0f), Spot("后花园", -38.0f, -3.0f), Spot("后花园", -37.5f, -10.0f), Spot("B2", -42.0f, -19.0f), Spot("B洞口", -47.3f, -49.6f),
        Spot("B门", -33.7f, -56.0f), Spot("B窗", -32.3f, -68.4f), Spot("B包点", -41.0f, -64.0f), Spot("B包点", -46.5f, -67.5f)
    )
    private class Box(val name: String, val x0: Float, val x1: Float, val z0: Float, val z1: Float) { val area = (x1 - x0) * (z1 - z0) }
    @Volatile private var boxes: List<Box>? = null

    /** A named box on the map, in display metres. */
    class Place(val name: String, val x0: Float, val x1: Float, val z0: Float, val z1: Float)

    /** The current map's own places, or null for Dust II's list. Read from the assets by [CalloutsLoader]. */
    fun use(places: List<Place>?) { boxes = places?.map { Box(it.name, it.x0, it.x1, it.z0, it.z1) } }

    private fun within(list: List<Box>, x: Float, z: Float): String {
        var inside: Box? = null; var close: Box? = null; var d = Float.MAX_VALUE
        for (b in list) {
            val dx = maxOf(b.x0 - x, 0f, x - b.x1); val dz = maxOf(b.z0 - z, 0f, z - b.z1); val q = dx * dx + dz * dz
            if (q == 0f) { if (inside == null || b.area < inside.area) inside = b } else if (q < d) { d = q; close = b }
        }
        return (inside ?: close)?.name ?: ""
    }

    fun near(x: Float, z: Float): String {
        boxes?.let { return within(it, x, z) }
        var best = spots[0]; var d = Float.MAX_VALUE
        for (s in spots) { val dx = s.x - x; val dz = s.z - z; val q = dx * dx + dz * dz; if (q < d) { d = q; best = s } }
        return best.name
    }
    /** "匪家丢中门" for a grenade thrown at [from] that came down at [to]; just the place when both are the same. */
    fun route(fromX: Float, fromZ: Float, toX: Float, toZ: Float): String {
        val a = near(fromX, fromZ); val b = near(toX, toZ)
        return if (a == b) "${a}就近" else "${a}丢$b"
    }
}

/** Where this grenade ended up doing its work: the smoke or fire itself, else where it burst. */
val Replay.Nade.landing get() = if ((kind == 0 || kind == 3) && fxStart > 0) fx else points[points.size - 1]
