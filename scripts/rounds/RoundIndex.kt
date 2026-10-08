// Round facts for the app's round filter, read from parsed replays (.nar) with the app's own reader (Replay.kt here).
//
//   RoundIndexKt <out-dir> <jobs.tsv>
//
// Mirage's place names are read from $ROUNDS_PLACES/de_mirage.json (default ./places).
// Each line of jobs.tsv is: match id, local .nar path, team1, team2 (tab-separated, the names the replay list uses).
// For each one <out-dir>/<match id>.json is written: one entry per round with what the filter asks about. Matches that
// cannot be read are reported as GitHub ::warning:: lines and skipped. build_rounds.py adds the list's own fields.
//
// Economy is the app's (replay/Analysis.kt): each side's equipment value at the end of freeze time (weapons, armour,
// kit, grenades at buy-menu prices). Pistol rounds are the first of each half (rounds 1 and 13); otherwise under $7,000
// is an eco, $17,000 or more with at least three rifles ($2,700 and up: AK, M4, AUG, SG, AWP, autos) a full buy, and
// anything between a force buy.
import com.ali.cs2utility.replay.Replay
import java.io.File
import kotlin.math.hypot

private const val ECO = 7000; private const val FULL = 17000; private const val RIFLES = 3

/** What a weapon costs in the buy menu (Analysis.price in the app). */
private fun price(code: Int) = when (code) {
    1, 2, 9 -> 200; 3, 6 -> 300; 4 -> 700; 5, 7, 8 -> 500; 10 -> 600
    21, 27 -> 1500; 22 -> 1250; 23 -> 1400; 24 -> 1050; 25 -> 1200; 26 -> 2350
    41 -> 1100; 42 -> 1050; 43 -> 1300; 44 -> 2000; 45 -> 5200; 46 -> 1700
    61 -> 1800; 62 -> 1950; 63 -> 2700; 64, 65 -> 2900; 66 -> 1700; 67 -> 3000; 68 -> 3300; 69 -> 4750; 70, 71 -> 5000
    else -> 0
}

/** The value of everything [slot] carries at sample [i] (Analysis.equipment in the app). */
private fun equipment(r: Replay.Round, slot: Int, i: Int): Int {
    val o = i * r.slots + slot
    if (r.flags[o].toInt() and Replay.PRESENT == 0) return 0
    var v = price(r.primary[o].toInt() and 255) + price(r.pistol[o].toInt() and 255)
    val gear = r.gear[o].toInt()
    if ((r.armor[o].toInt() and 255) > 0) v += if (gear and Replay.HELMET != 0) 1000 else 650
    if (gear and Replay.KIT != 0) v += 400
    val g = r.grenades[o].toInt() and 255
    if (g and Replay.G_SMOKE != 0) v += 300
    if (g and Replay.G_HE != 0) v += 300
    if (g and Replay.G_MOLOTOV != 0) v += 400
    if (g and Replay.G_INCENDIARY != 0) v += 500
    if (g and Replay.G_DECOY != 0) v += 50
    v += ((g shr 4) and 3) * 200
    return v
}

/**
 * Which bomb site a plant at Source position ([x], [y], [z]) is on. The replay keeps where the planter stood, not the
 * site, so each map's two sites are told apart by one coordinate: every plant in the library falls into two clear
 * clusters either side of these lines. Which cluster is A comes from the map layouts: Dust II, Mirage, Inferno and
 * Nuke are certain; on Ancient A is the site nearer CT spawn, on Anubis and Cache B is (less certain: check these
 * three against a replay if a site looks swapped). Empty for a map not listed.
 */
fun site(map: String, x: Float, y: Float, z: Float): String = when {
    map.contains("dust2") -> if (x > -300f) "A" else "B"
    map.contains("mirage") -> if (y < -800f) "A" else "B"
    map.contains("inferno") -> if (y < 1500f) "A" else "B"
    map.contains("nuke") -> if (z > -600f) "A" else "B"
    map.contains("ancient") -> if (x < -300f) "A" else "B"
    map.contains("anubis") -> if (x > -100f) "A" else "B"
    map.contains("cache") -> if (y < 0f) "A" else "B"
    else -> ""
}

private fun norm(s: String) = s.lowercase().replace(Regex("[^a-z0-9]"), "").removePrefix("team").removeSuffix("esports").removeSuffix("gaming")
/** How alike an in-game clan name is to a team's listed name: 3 the same, 2 one inside the other, 1 same start, 0 nothing. */
fun alike(clan: String, team: String): Int {
    val a = norm(clan); val b = norm(team)
    if (a.isEmpty() || b.isEmpty()) return 0
    return when { a == b -> 3; a.contains(b) || b.contains(a) -> 2; a.take(3) == b.take(3) -> 1; else -> 0 }
}

private fun q(s: String) = buildString {
    append('"'); for (ch in s) when (ch) { '"' -> append("\\\""); '\\' -> append("\\\\"); '\n' -> append("\\n"); else -> if (ch < ' ') append(' ') else append(ch) }; append('"')
}

/**
 * How a map is laid out for reading the attackers' play, in the app's own place names ([Callouts]): which places are each
 * bomb site, which approach each other place belongs to, and where being means a side has committed to a site.
 */
private class Layout(val sites: Map<String, Set<String>>, val routes: Map<String, String>, val commit: Map<String, Set<String>>)

private val LAYOUTS = mapOf(
    // Dust II's sites as replay/Analysis.kt draws them, its approaches as Analysis.plan names them.
    "dust2" to Layout(
        mapOf("A" to setOf("A包点", "A平台", "A大过点"), "B" to setOf("B包点", "B窗")),
        mapOf("A大" to "A大", "蓝车" to "A大", "A大门" to "A大", "A外" to "A大", "A小" to "A小", "Xbox" to "A小",
            "B洞口" to "B洞", "B2" to "B洞", "B1" to "B洞", "后花园" to "B洞", "中门" to "中路", "警家中路" to "中路", "B门" to "中路"),
        mapOf("A" to setOf("A大", "蓝车", "A小"), "B" to setOf("B洞口", "B门"))),
    // Mirage's places are the map's own (env_cs_place); A main is A1 and A2通道, palace A2楼, apartments B二楼/B2/B通道.
    "mirage" to Layout(
        mapOf("A" to setOf("A包点", "脚手架"), "B" to setOf("B包点", "B卡车")),
        mapOf("A1" to "A大", "A2通道" to "A大", "A2楼" to "二楼", "Jungle" to "中路", "A楼梯" to "中路", "拱门" to "中路", "中路" to "中路",
            "中路匪口" to "中路", "下水道" to "中路", "B二楼" to "B二楼", "B2" to "B二楼", "B通道" to "B二楼", "B小" to "B小", "黑屋" to "B小", "VIP" to "B小"),
        mapOf("A" to setOf("A1", "A2通道", "A2楼"), "B" to setOf("B二楼", "B小"))))

/** Mirage's place boxes, read once from places/de_mirage.json (the app's assets/maps/mirage/places.json). */
private val miragePlaces: List<com.ali.cs2utility.replay.Callouts.Place> by lazy {
    val text = File(System.getenv("ROUNDS_PLACES") ?: "places", "de_mirage.json").readText()
    Regex("\"name\":\\s*\"([^\"]+)\",\\s*\"box\":\\s*\\[([^\\]]+)]").findAll(text.substringBefore("\"sites\"")).map { m ->
        val b = m.groupValues[2].split(',').map { it.trim().toFloat() }
        com.ali.cs2utility.replay.Callouts.Place(m.groupValues[1], b[0], b[1], b[4], b[5])
    }.toList()
}

/** Points [Callouts] at [map]'s place names; the layout to read it with, or null for a map the app has no names for. */
private fun layout(map: String): Layout? {
    val key = LAYOUTS.keys.firstOrNull { map.contains(it) } ?: return null
    com.ali.cs2utility.replay.Callouts.use(if (key == "dust2") null else miragePlaces)
    return LAYOUTS[key]
}

/**
 * How the attackers (T) played the round, read from where they were every half second from the end of freeze time
 * until the bomb went down (or the round was decided):
 *  - the target is the plant's site, else the site at least two of them set foot on (the one more of them did), else none;
 *  - their hit is the first time one of them stood on the target site, with everyone who got there within 12 s of it;
 *  - each one's way in is the approach of the last place on one of the map's approaches they passed in the 20 s before
 *    stepping on the site (places off every approach, like CT spawn, are passed over);
 *  - "rotate" (转点): at some moment from 10 s after freeze time to 4 s before the hit, three or more of them were alive
 *    on the other site or its last approaches;
 *  - else "split" (夹击): three or more in the hit, through two or more ways in;
 *  - else "rush" (爆弹): three of them (or all alive, if fewer) on the site within 40 s of freeze time ending;
 *  - else "default" (控图): a slower round that hit the site later;
 *  - "none": nobody went onto a site. The JSON gives the class, the site, the hit's second and the ways in.
 */
private fun attack(rp: Replay, r: Replay.Round, plantSite: String, plantTick: Int, lay: Layout): String {
    val n = r.slots; val rate = rp.tickRate
    val until = if (plantTick > 0) plantTick else r.decided
    val ts = (0 until n).filter { r.team[it] == 2 }
    // Where each attacker was, sample by sample: (tick, place) while alive.
    val track = ts.associateWith { ArrayList<Pair<Int, String>>() }
    var i = r.sampleAt(r.freezeEnd.toFloat())
    while (i < r.ticks.size && r.ticks[i] <= until) {
        for (s in ts) { val o = i * n + s
            if (r.flags[o].toInt() and (Replay.PRESENT or Replay.ALIVE) == (Replay.PRESENT or Replay.ALIVE))
                track[s]!!.add(r.ticks[i] to com.ali.cs2utility.replay.Callouts.near(r.x[o], r.z[o])) }
        i += 8
    }
    fun entries(site: String) = ts.mapNotNull { s -> track[s]!!.firstOrNull { it.second in lay.sites[site]!! }?.let { s to it.first } }
    val target = plantSite.takeIf { it == "A" || it == "B" }
        ?: listOf("A", "B").map { it to entries(it).size }.filter { it.second >= 2 }.maxByOrNull { it.second }?.first
        ?: return "{\"k\":\"none\"}"
    val entered = entries(target).sortedBy { it.second }
    if (entered.isEmpty()) return "{\"k\":\"none\",\"site\":${q(target)}}"
    val hit = entered[0].second
    val group = entered.filter { it.second <= hit + rate * 12f }
    fun way(s: Int, tick: Int): String? = track[s]!!.lastOrNull { it.first < tick && it.first >= tick - rate * 20f && it.second in lay.routes }
        ?.second?.let { lay.routes[it] }
    val ways = group.mapNotNull { way(it.first, it.second) }.distinct()
    val other = if (target == "A") "B" else "A"
    val near = lay.commit[other]!! + lay.sites[other]!!
    var rotated = false
    i = r.sampleAt(r.freezeEnd + rate * 10f)
    while (!rotated && i < r.ticks.size && r.ticks[i] <= hit - rate * 4f) {
        var count = 0
        for (s in ts) { val o = i * n + s
            if (r.flags[o].toInt() and (Replay.PRESENT or Replay.ALIVE) == (Replay.PRESENT or Replay.ALIVE) && com.ali.cs2utility.replay.Callouts.near(r.x[o], r.z[o]) in near) count++ }
        if (count >= 3) rotated = true
        i += 8
    }
    val aliveAtStart = ts.count { track[it]!!.isNotEmpty() }
    val early = entered.count { it.second <= r.freezeEnd + rate * 40f }
    val kind = when {
        rotated -> "rotate"
        group.size >= 3 && ways.size >= 2 -> "split"
        early >= minOf(3, aliveAtStart.coerceAtLeast(1)) -> "rush"
        else -> "default"
    }
    return "{\"k\":${q(kind)},\"site\":${q(target)},\"t\":${((hit - r.freezeEnd) / rate).toInt().coerceAtLeast(0)},\"via\":[${ways.joinToString(",") { q(it) }}]}"
}

/** Every round's facts, as the JSON written for one match; the warnings found on the way go to [warn]. */
fun facts(rp: Replay, team1: String, team2: String, warn: (String) -> Unit): String {
    val rounds = rp.rounds; val n = rp.players.size
    // The two line-ups, by player slot: the slots on CT in the first round are one team, the rest the other.
    val first = rounds.first()
    val groupOf = IntArray(n) { s -> when (first.team[s]) { 3 -> 1; 2 -> 2; else -> 0 } }
    // A slot that sat out the first round joins the group it is first seen with.
    for (r in rounds) for (s in 0 until n) if (groupOf[s] == 0 && r.team[s] in 2..3) {
        val mates = (0 until n).filter { it != s && r.team[it] == r.team[s] && groupOf[it] != 0 }
        if (mates.isNotEmpty()) groupOf[s] = mates.groupingBy { groupOf[it] }.eachCount().maxByOrNull { it.value }!!.key
    }
    /** Which group was on CT in [r]: the one with more of its players there. */
    fun ctGroup(r: Replay.Round): Int {
        var one = 0; var two = 0
        for (s in 0 until n) if (r.team[s] == 3) { if (groupOf[s] == 1) one++ else if (groupOf[s] == 2) two++ }
        return if (one >= two) 1 else 2
    }
    // Which group is team1: by the clan names the game gave each side, against the list's names.
    var vote = 0; val clans = arrayOf(HashMap<String, Int>(), HashMap<String, Int>())
    for (r in rounds) {
        val g = ctGroup(r); val ctName = r.nameCT; val tName = r.nameT
        val one = if (g == 1) ctName else tName; val two = if (g == 1) tName else ctName
        clans[0].merge(one, 1, Int::plus); clans[1].merge(two, 1, Int::plus)
        vote += alike(one, team1) + alike(two, team2) - alike(one, team2) - alike(two, team1)
    }
    val clan1 = clans[0].maxByOrNull { it.value }?.key.orEmpty(); val clan2 = clans[1].maxByOrNull { it.value }?.key.orEmpty()
    val swapped = vote < 0
    if (vote == 0) warn("cannot tell which side is $team1 (clans '$clan1' / '$clan2'); team left unknown")
    fun teamOf(group: Int) = if (vote == 0) 0 else if ((group == 1) != swapped) 1 else 2

    val lay = layout(rp.map)
    val out = StringBuilder()
    out.append("{\"clans\":[").append(q(if (swapped) clan2 else clan1)).append(',').append(q(if (swapped) clan1 else clan2)).append("],\"rounds\":[")
    for ((li, r) in rounds.withIndex()) {
        val i = r.sampleAt(r.freezeEnd.toFloat())
        val firstDeath = r.kills.minOfOrNull { it.tick } ?: Int.MAX_VALUE
        val late = r.sampleAt(minOf(r.freezeEnd + rp.tickRate * 5f, firstDeath - 1f)).coerceAtLeast(i)
        // Economy when freeze time ended, CT first.
        val value = IntArray(4); val rifles = IntArray(4); val alive = IntArray(4)
        val gear = arrayOf(ArrayList<Int>(), ArrayList<Int>())
        for (s in 0 until r.slots) {
            val side = r.team[s]; if (side != 2 && side != 3) continue
            val o = i * r.slots + s; if (r.flags[o].toInt() and Replay.PRESENT == 0) continue
            alive[side]++; value[side] += equipment(r, s, i)
            if (price(r.primary[o].toInt() and 255) >= 2700) rifles[side]++
            // Weapons a few seconds later, before anyone has died: a rifle bought late or passed over still counts.
            val q = late * r.slots + s; val on = r.flags[q].toInt() and Replay.PRESENT != 0
            val p = (if (on) r.primary[q] else r.primary[o]).toInt() and 255; val h = (if (on) r.pistol[q] else r.pistol[o]).toInt() and 255
            val list = gear[if (side == 3) 0 else 1]; if (p != 0) list.add(p); if (h != 0) list.add(h)
        }
        val pistolRound = r.index == 0 || r.index == 12
        fun buy(side: Int) = when { pistolRound -> 0; value[side] < ECO -> 1; rifles[side] >= RIFLES && value[side] >= FULL -> 3; else -> 2 }
        // Every count of players the round went through, CT then T, up to the moment it was decided.
        val states = StringBuilder().append(alive[3].coerceAtMost(9)).append(alive[2].coerceAtMost(9))
        for (k in r.kills.sortedBy { it.tick }) {
            if (k.tick > r.decided) break
            val side = r.team.getOrElse(k.victim) { 0 }; if (side != 2 && side != 3 || alive[side] == 0) continue
            alive[side]--; states.append(alive[3].coerceAtMost(9)).append(alive[2].coerceAtMost(9))
        }
        // The bomb: where it went down and who planted it, and how that ended.
        val plant = r.bomb.firstOrNull { it.kind == 0 }
        val defused = r.bomb.any { it.kind == 1 }; val exploded = r.bomb.any { it.kind == 2 }
        fun nearest(tick: Int, side: Int, x: Float, z: Float): String {
            val j = r.sampleAt(tick.toFloat()); var best = -1; var d = Float.MAX_VALUE
            for (s in 0 until r.slots) if (r.team[s] == side) { val o = j * r.slots + s
                if (r.flags[o].toInt() and Replay.PRESENT == 0) continue
                val e = hypot(r.x[o] - x, r.z[o] - z); if (e < d) { d = e; best = s } }
            return if (best >= 0 && d < 4f) rp.players[best] else ""
        }
        val winner = r.winner
        val loser = if (winner == 3) 2 else if (winner == 2) 3 else 0
        val why = when {
            exploded -> "e"; defused -> "d"
            loser != 0 && states.length >= 2 && states[states.length - (if (loser == 3) 2 else 1)] == '0' -> "k"
            r.reason == 12 -> "t"; r.reason == 16 || r.reason == 17 -> "s"
            r.reason == 1 -> "e"; r.reason == 7 -> "d"; r.reason == 8 || r.reason == 9 -> "k"
            else -> ""
        }
        val g = ctGroup(r); val ct = teamOf(g)
        val s1 = if (ct == 2) r.startT else r.startCT; val s2 = if (ct == 2) r.startCT else r.startT
        if (li > 0) out.append(',')
        out.append("{\"i\":").append(li).append(",\"n\":").append(r.index + 1).append(",\"ct\":").append(ct).append(",\"w\":").append(winner)
            .append(",\"why\":").append(q(why)).append(",\"s\":[").append(s1).append(',').append(s2).append(']')
            .append(",\"buy\":[").append(buy(3)).append(',').append(buy(2)).append("],\"val\":[").append(value[3]).append(',').append(value[2]).append(']')
            .append(",\"eq\":[[").append(gear[0].sorted().joinToString(",")).append("],[").append(gear[1].sorted().joinToString(",")).append("]]")
            .append(",\"al\":").append(q(states.toString()))
            .append(",\"t\":").append(((r.decided - r.freezeEnd) / rp.tickRate).toInt().coerceAtLeast(0))
        val plantSite = plant?.let { site(rp.map, it.position.x / Replay.UNIT, -it.position.z / Replay.UNIT, it.position.y / Replay.UNIT) }.orEmpty()
        if (lay != null) out.append(",\"atk\":").append(attack(rp, r, plantSite, plant?.tick ?: 0, lay))
        if (plant != null) {
            val p = plant.position
            // Back to Source units: the reader turns them into display metres with Y up.
            val where = plantSite
            out.append(",\"b\":{\"site\":").append(q(where)).append(",\"by\":").append(q(nearest(plant.tick, 2, p.x, p.z)))
                .append(",\"at\":").append(((plant.tick - r.freezeEnd) / rp.tickRate).toInt().coerceAtLeast(0))
                .append(",\"end\":").append(q(if (defused) "d" else if (exploded) "e" else ""))
            r.bomb.firstOrNull { it.kind == 1 }?.let { b -> out.append(",\"def\":").append(q(nearest(b.tick, 3, b.position.x, b.position.z))) }
            out.append('}')
        }
        out.append('}')
    }
    out.append("]}")
    return out.toString()
}

fun main(args: Array<String>) {
    val dir = File(args[0]).apply { mkdirs() }
    val probe = System.getenv("ROUNDS_PROBE") == "1"
    for (line in File(args[1]).readLines()) {
        val f = line.split('\t'); if (f.size < 4) continue
        val (id, path, team1, team2) = f
        val result = runCatching {
            val rp = File(path).inputStream().use { Replay.read(it) }
            val warnings = ArrayList<String>()
            val json = facts(rp, team1, team2) { warnings.add(it) }
            for (w in warnings) println("::warning::$id: $w")
            if (probe) for (r in rp.rounds) r.bomb.firstOrNull { it.kind == 0 }?.let { b ->
                println("PLANT\t${rp.map}\t${b.position.x / Replay.UNIT}\t${-b.position.z / Replay.UNIT}\t${b.position.y / Replay.UNIT}") }
            if (probe) for (r in rp.rounds) for (s in 0 until r.slots) if (r.team[s] in 2..3 && r.flags[s].toInt() and Replay.PRESENT != 0)
                println("SPAWN\t${rp.map}\t${r.team[s]}\t${r.x[s] / Replay.UNIT}\t${-r.z[s] / Replay.UNIT}")
            File(dir, "$id.json").writeText(json)
            println("$id: ${rp.rounds.size} rounds")
        }
        result.onFailure { println("::warning::$id: cannot read the replay: ${it.message}") }
    }
}
