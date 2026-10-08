// Vendored verbatim from the app (app/src/main/java/com/ali/cs2utility/replay/Tactic.kt): the canonical names of the
// attackers' play, shared by the replay analysis, this index and the app's round filter.
package com.ali.cs2utility.replay

/**
 * How the attackers (T) played a round, by one set of names used everywhere: the round analysis in a replay
 * ([Analysis.plan]), the demo service's round index (its generator compiles this very file) and the round filter. A
 * round is "A 爆弹" or "B 夹击" whichever of them shows it, so a play seen in one replay is found by the same name across
 * all of them.
 *
 * Read from where the Ts were every half second from the end of freeze time until the bomb went down (or the round was
 * decided), in the map's place names ([Callouts]); only maps whose places the app names have a [Layout] (Dust II and
 * Mirage), the others are [Kind.UNKNOWN]:
 *  - the target is the plant's site, else the site at least two of them set foot on (the one more of them did), else none;
 *  - the hit is the first time one of them stood on the target site, with everyone who got there within 12 s of it;
 *  - each one's way in is the approach of the last place on one of the map's approaches they passed in the 20 s before
 *    stepping on the site (places off every approach, like CT spawn, are passed over);
 *  - [Kind.ROTATE] 转点: from 10 s after freeze time to 4 s before the hit, three or more of them were at once on the other
 *    site or its last approaches;
 *  - else [Kind.SPLIT] 夹击: three or more in the hit, through two or more ways in;
 *  - else [Kind.RUSH] 爆弹: three of them (or all alive, if fewer) on the site within 40 s of freeze time ending;
 *  - else [Kind.DEFAULT] 控图: a slower round that took the map first and hit the site later;
 *  - [Kind.NONE] 未进攻: nobody went onto a site.
 */
object Tactic {
    /** The ids are what the round index stores; the labels are what every screen shows. */
    enum class Kind(val id: String, val label: String) {
        DEFAULT("default", "控图"), RUSH("rush", "爆弹"), SPLIT("split", "夹击"), ROTATE("rotate", "转点"), NONE("none", "未进攻"), UNKNOWN("", "");
        companion object { fun of(id: String) = entries.firstOrNull { it.id == id } ?: UNKNOWN }
    }

    /** One round's play: what kind, at which site ("A", "B" or ""), the second of the hit after freeze time, and the ways in. */
    class Play(val kind: Kind, val site: String, val seconds: Int, val via: List<String>) {
        /** The canonical name: "A 爆弹", "B 夹击", "未进攻"; empty when not known. */
        val title get() = name(kind, site)
    }
    fun name(kind: Kind, site: String) = when {
        kind == Kind.UNKNOWN -> ""
        kind == Kind.NONE || site.isEmpty() -> kind.label
        else -> "$site ${kind.label}"
    }

    /** Which places are each bomb site, which approach each other place belongs to, and where being means having committed to a site. */
    class Layout(val sites: Map<String, Set<String>>, val routes: Map<String, String>, val commit: Map<String, Set<String>>)

    private val LAYOUTS = mapOf(
        // Dust II's sites as the analysis has always drawn them, and its approaches.
        "dust2" to Layout(
            mapOf("A" to setOf("A包点", "A平台", "A大过点"), "B" to setOf("B包点", "B窗")),
            mapOf("A大" to "A大", "蓝车" to "A大", "A大门" to "A大", "A外" to "A大", "A小" to "A小", "Xbox" to "A小",
                "B洞口" to "B洞", "B2" to "B洞", "B1" to "B洞", "后花园" to "B洞", "中门" to "中路", "警家中路" to "中路", "B门" to "中路"),
            mapOf("A" to setOf("A大", "蓝车", "A小"), "B" to setOf("B洞口", "B门"))),
        // Mirage's places are the map's own (env_cs_place): A main is A1 and A2通道, palace A2楼, apartments B二楼, B2, B通道.
        "mirage" to Layout(
            mapOf("A" to setOf("A包点", "脚手架"), "B" to setOf("B包点", "B卡车")),
            mapOf("A1" to "A大", "A2通道" to "A大", "A2楼" to "二楼", "Jungle" to "中路", "A楼梯" to "中路", "拱门" to "中路", "中路" to "中路",
                "中路匪口" to "中路", "下水道" to "中路", "B二楼" to "B二楼", "B2" to "B二楼", "B通道" to "B二楼", "B小" to "B小", "黑屋" to "B小", "VIP" to "B小"),
            mapOf("A" to setOf("A1", "A2通道", "A2楼"), "B" to setOf("B二楼", "B小"))))

    /** The layout for [map], or null when the app names no places on it. [Callouts] must already be using that map's places. */
    fun layout(map: String): Layout? = LAYOUTS.entries.firstOrNull { map.contains(it.key) }?.value

    /**
     * Which bomb site a plant at [p] (display metres, as [Replay.Bomb.position]: where the planter stood) is on. Each map's
     * two sites are told apart by one Source coordinate: every plant in the service's library falls into two clear
     * clusters either side of these lines. Dust II, Mirage, Inferno and Nuke are certain; on Ancient A is the site nearer
     * CT spawn, on Anubis and Cache B is (less certain). Empty for a map not listed.
     */
    fun bombSite(map: String, p: com.ali.cs2utility.domain.Vec3): String {
        val x = p.x / Replay.UNIT; val y = -p.z / Replay.UNIT; val z = p.y / Replay.UNIT
        return when {
            map.contains("dust2") -> if (x > -300f) "A" else "B"
            map.contains("mirage") -> if (y < -800f) "A" else "B"
            map.contains("inferno") -> if (y < 1500f) "A" else "B"
            map.contains("nuke") -> if (z > -600f) "A" else "B"
            map.contains("ancient") -> if (x < -300f) "A" else "B"
            map.contains("anubis") -> if (x > -100f) "A" else "B"
            map.contains("cache") -> if (y < 0f) "A" else "B"
            else -> ""
        }
    }

    /** How the Ts played [r]; [Kind.UNKNOWN] on a map without a [layout]. */
    fun read(rp: Replay, r: Replay.Round): Play {
        val lay = layout(rp.map) ?: return Play(Kind.UNKNOWN, r.bomb.firstOrNull { it.kind == 0 }?.let { bombSite(rp.map, it.position) }.orEmpty(), 0, emptyList())
        val plant = r.bomb.firstOrNull { it.kind == 0 }
        val plantSite = plant?.let { bombSite(rp.map, it.position) }.orEmpty()
        val n = r.slots; val rate = rp.tickRate
        val until = plant?.tick ?: r.decided
        val ts = (0 until n).filter { r.team[it] == 2 }
        fun up(o: Int) = r.flags[o].toInt() and (Replay.PRESENT or Replay.ALIVE) == (Replay.PRESENT or Replay.ALIVE)
        // Where each attacker was, sample by sample: (tick, place) while alive.
        val track = ts.associateWith { ArrayList<Pair<Int, String>>() }
        var i = r.sampleAt(r.freezeEnd.toFloat())
        while (i < r.ticks.size && r.ticks[i] <= until) {
            for (s in ts) { val o = i * n + s; if (up(o)) track.getValue(s).add(r.ticks[i] to Callouts.near(r.x[o], r.z[o])) }
            i += 8
        }
        fun entries(site: String) = ts.mapNotNull { s -> track.getValue(s).firstOrNull { it.second in lay.sites.getValue(site) }?.let { s to it.first } }
        val target = plantSite.takeIf { it == "A" || it == "B" }
            ?: listOf("A", "B").map { it to entries(it).size }.filter { it.second >= 2 }.maxByOrNull { it.second }?.first
            ?: return Play(Kind.NONE, "", 0, emptyList())
        val entered = entries(target).sortedBy { it.second }
        if (entered.isEmpty()) return Play(Kind.NONE, target, 0, emptyList())
        val hit = entered[0].second
        val group = entered.filter { it.second <= hit + rate * 12f }
        fun way(s: Int, tick: Int): String? = track.getValue(s).lastOrNull { it.first < tick && it.first >= tick - rate * 20f && it.second in lay.routes }
            ?.second?.let { lay.routes[it] }
        val ways = group.mapNotNull { way(it.first, it.second) }.distinct()
        val other = if (target == "A") "B" else "A"
        val near = lay.commit.getValue(other) + lay.sites.getValue(other)
        var rotated = false
        i = r.sampleAt(r.freezeEnd + rate * 10f)
        while (!rotated && i < r.ticks.size && r.ticks[i] <= hit - rate * 4f) {
            if (ts.count { s -> val o = i * n + s; up(o) && Callouts.near(r.x[o], r.z[o]) in near } >= 3) rotated = true
            i += 8
        }
        val alive = ts.count { track.getValue(it).isNotEmpty() }
        val early = entered.count { it.second <= r.freezeEnd + rate * 40f }
        val kind = when {
            rotated -> Kind.ROTATE
            group.size >= 3 && ways.size >= 2 -> Kind.SPLIT
            early >= minOf(3, alive.coerceAtLeast(1)) -> Kind.RUSH
            else -> Kind.DEFAULT
        }
        return Play(kind, target, ((hit - r.freezeEnd) / rate).toInt().coerceAtLeast(0), ways)
    }

}
