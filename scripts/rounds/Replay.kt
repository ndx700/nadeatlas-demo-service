// Vendored from the app (ndx700/nade-atlas-claude, app/src/main/java/com/ali/cs2utility/replay/Replay.kt): the .nar
// reader, without the grenade-lesson builder that follows it there. Only change: the round-end reason byte is kept
// (Round.reason). Copy it again when the app changes the format.
package com.ali.cs2utility.replay

import com.ali.cs2utility.domain.Vec3
import java.io.DataInputStream
import java.io.InputStream
import java.util.zip.GZIPInputStream
import kotlin.math.*

/**
 * A match read from a CS2 demo by the bundled converter (demo/main.go), ready to play back.
 *
 * File: gzip of big-endian data. "NAR2", map name, tick rate, players (name, steam id), then per
 * round: start / freeze-end / end ticks, winner, reason, score after the round, the two team
 * names, team and kills / deaths / assists so far of each player slot, samples (16 a second:
 * slot, x y z in 1/8 unit, yaw, pitch, health, flags, held weapon, armour, gear, money, rounds in
 * the clip, scope zoom step, grenades, primary, pistol), grenades (kind, thrower, flags, eye, yaw, pitch, effect
 * start / end / centre, trajectory points, fire patches), kills, shots and bomb events. After the
 * last round an optional "VOX1" block holds the voice chat: tick, slot and one Opus packet each; then an optional
 * "PUN1" block: per round, where each shot went (yaw and pitch with the recoil added); then an optional "DRP1" block:
 * per round, everything let go of (weapon code, who let go, who took it, start and end tick, its path).
 * "NAR1" files from the first converter lack the names, the running stats and everything after
 * the held weapon. Positions are Source units in the file and display metres (Y up) once loaded.
 */
class Replay(val map: String, val tickRate: Float, val players: List<String>, val rounds: List<Round>, val voice: Voice = Voice.NONE) {
    /**
     * In-game voice chat, when the demo carried any: Opus packets of 10 ms at 48 kHz, one speaker
     * each, in tick order. Matches played with voice outside the game have none.
     */
    class Voice(val ticks: IntArray, val slots: ByteArray, val packets: Array<ByteArray>) {
        val size get() = ticks.size
        /** Index of the first packet at or after [tick]. */
        fun first(tick: Int): Int { var lo = 0; var hi = ticks.size; while (lo < hi) { val mid = (lo + hi) ushr 1; if (ticks[mid] < tick) lo = mid + 1 else hi = mid }; return lo }
        /** Bit per slot of everyone with a packet in the [window] ticks up to [tick]: who is talking right now. */
        fun speaking(tick: Int, window: Int): Int {
            var mask = 0; var i = first(tick - window)
            while (i < ticks.size && ticks[i] <= tick) { mask = mask or (1 shl (slots[i].toInt() and 31)); i++ }
            return mask
        }
        companion object { val NONE = Voice(IntArray(0), ByteArray(0), emptyArray()) }
    }

    class Round(
        val index: Int, val start: Int, val freezeEnd: Int, val end: Int, val winner: Int,
        /** The score once this round was decided, and the teams on each side while it was played. */
        val scoreCT: Int, val scoreT: Int, val nameCT: String, val nameT: String,
        /** Team of each player slot this round: 2 T, 3 CT, 0 not playing. */
        val team: IntArray,
        /** Kills, deaths and assists of each slot when the round began, at [slot * 3]. */
        val before: IntArray,
        val ticks: IntArray,
        // One entry per sample per slot, at [sample * slots + slot].
        val x: FloatArray, val y: FloatArray, val z: FloatArray, val yaw: FloatArray, val pitch: ByteArray,
        val health: ByteArray, val flags: ByteArray, val weapon: ByteArray,
        val armor: ByteArray, val gear: ByteArray, val money: ShortArray, val clip: ByteArray,
        /** How far a telescopic sight is zoomed in: 0, 1 or 2. Files from before this was recorded have 0 throughout. */
        val zoom: ByteArray,
        val grenades: ByteArray, val primary: ByteArray, val pistol: ByteArray,
        val nades: List<Nade>, val kills: List<Kill>, val shots: IntArray, val bomb: List<Bomb>, private val rate: Float
    ) {
        val slots = team.size
        /** Why the round ended, as the demo parser numbers it (vendored copy only: the app skips this byte). */
        var reason = 0
        /** Where each of [shots] went, yaw then pitch in degrees, recoil included; null in files from before it was recorded. */
        var aims: FloatArray? = null
        /** Everything let go of this round, as it flew and where it lay; null in files from before it was recorded. */
        var loose: List<Loose>? = null
        /** The score while this round was being played. */
        val startCT get() = scoreCT - if (winner == 3) 1 else 0
        val startT get() = scoreT - if (winner == 2) 1 else 0
        /** The tick the round was decided at; the converter keeps four seconds of aftermath past it. */
        val decided: Int get() = (end - rate * 4f).toInt().coerceAtLeast(freezeEnd)
        val duration get() = (end - start) / rate
        fun seconds(tick: Int) = (tick - start) / rate
        fun tick(seconds: Float) = start + seconds * rate
        private var deaths: IntArray? = null
        /** The tick [slot] died at this round, or -1. */
        fun deathTick(slot: Int): Int {
            val d = deaths ?: IntArray(slots) { -1 }.also { out ->
                for (k in kills) if (k.victim in 0 until slots) out[k.victim] = k.tick
                // Deaths without a kill event (the bomb, a fall): the first sample they are no longer alive in.
                for (s in 0 until slots) if (out[s] < 0) {
                    var seen = false
                    for (i in ticks.indices) { val fl = flags[i * slots + s].toInt()
                        if (fl and ALIVE != 0) seen = true else if (seen && fl and PRESENT != 0) { out[s] = ticks[i]; break } }
                }
                deaths = out
            }
            return d[slot]
        }
        /** Index of the last sample at or before [tick]. */
        fun sampleAt(tick: Float): Int {
            var lo = 0; var hi = ticks.size - 1
            if (hi < 0 || tick <= ticks[0]) return 0
            if (tick >= ticks[hi]) return hi
            while (hi - lo > 1) { val mid = (lo + hi) ushr 1; if (ticks[mid] <= tick) lo = mid else hi = mid }
            return lo
        }
    }

    /** kind: 0 smoke, 1 flash, 2 HE, 3 molotov / incendiary, 4 decoy. */
    class Nade(
        val kind: Int, val thrower: Int,
        /** What the thrower was doing as it left the hand: 1 in the air, 2 crouched, 4 moving, 8 walking (shift), 16 W, 32 S, 64 A, 128 D. */
        val keys: Int,
        val eye: Vec3, val yaw: Float, val pitch: Float,
        val fxStart: Int, val fxEnd: Int, val fx: Vec3,
        ticks: IntArray, points: Array<Vec3>, val fires: Array<Vec3>
    ) {
        var ticks = ticks; private set
        var points = points; private set
        /** Puts a bounce the recording left out back into the flight, at [tick] (strictly between two known points). */
        fun restore(ticks: IntArray, points: Array<Vec3>) { this.ticks = ticks; this.points = points }
        fun insert(tick: Int, point: Vec3) {
            val k = ticks.indexOfFirst { it >= tick }; if (k <= 0 || ticks[k] == tick) return
            ticks = ticks.copyOfRange(0, k) + tick + ticks.copyOfRange(k, ticks.size)
            points = (points.take(k) + point + points.drop(k)).toTypedArray()
        }
        val jump get() = keys and 1 != 0
        val crouch get() = keys and 2 != 0
        val moving get() = keys and 4 != 0
        val thrown get() = ticks[0]
        /**
         * How hard it was thrown, from the speed it left the hand at: 1 a full left-click throw,
         * 0.5 both buttons, 0 a right-click lob. The game throws at 675, 439 and 203 units a second
         * and adds a share of the thrower's own speed, so the bands are wide apart.
         */
        val strength: Float get() {
            if (ticks.size < 2) return 1f
            val t = (ticks[1] - ticks[0]) / TICK
            if (t < 0.03f) return 1f
            val a = points[0]; val b = points[1]
            val vx = (b.x - a.x) / t; val vz = (b.z - a.z) / t; val vy = (b.y - a.y) / t + 0.5f * GRAVITY * t
            val speed = sqrt(vx * vx + vy * vy + vz * vz) / UNIT
            return when { speed > 590f -> 1f; speed > 330f -> 0.5f; else -> 0f }
        }
        /** Tick the grenade stops being a flying object: when its effect starts, else its last known point. */
        val landed get() = if (fxStart > thrown) fxStart else ticks[ticks.size - 1]

        /** Position at [tick] while in flight. Between two known points a grenade is in free fall, so the arc is exact. */
        fun at(tick: Float): Vec3 {
            if (tick <= ticks[0]) return points[0]
            val last = ticks.size - 1
            if (tick >= ticks[last]) return points[last]
            var i = 0
            while (i < last - 1 && ticks[i + 1] <= tick) i++
            val t0 = ticks[i]; val t1 = ticks[i + 1]
            val f = (tick - t0) / (t1 - t0).coerceAtLeast(1)
            val a = points[i]; val b = points[i + 1]
            val seconds = (t1 - t0) / TICK; val sag = if (a.distance(b) > 0.4f) 0.5f * GRAVITY * seconds * seconds * f * (1f - f) else 0f
            return Vec3(a.x + (b.x - a.x) * f, a.y + (b.y - a.y) * f + sag, a.z + (b.z - a.z) * f)
        }
    }

    class Kill(val tick: Int, val killer: Int, val victim: Int, val assister: Int, val weapon: Int, val flags: Int) {
        val headshot get() = flags and 1 != 0
        val wallbang get() = flags and 2 != 0
        val smoke get() = flags and 4 != 0
        val noScope get() = flags and 8 != 0
        val flashAssist get() = flags and 16 != 0
        val blind get() = flags and 32 != 0
    }
    /** kind: 0 planted, 1 defused, 2 exploded. */
    class Bomb(val tick: Int, val kind: Int, val position: Vec3)

    /**
     * Something a player let go of: a weapon or grenade thrown down for a teammate, or fallen from someone who died.
     * It flies along [points] (recorded 16 times a second, from the moment it left [from]) and then lies at the last
     * of them until [to] picks it up at [end], or it is gone at [end], or (end 0) the round is over.
     */
    class Loose(val code: Int, val from: Int, val to: Int, val start: Int, val end: Int, val ticks: IntArray, val points: Array<Vec3>) {
        /** When it came to rest. */
        val landed get() = ticks[ticks.size - 1]
        val rest get() = points[points.size - 1]
        /** Taken by someone other than whoever let go of it. */
        val passed get() = to >= 0 && to != from
        fun until(round: Round) = if (end > 0) end else round.end
        fun at(tick: Float): Vec3 {
            if (tick <= ticks[0]) return points[0]
            if (tick >= landed) return rest
            var k = 1; while (ticks[k] < tick) k++
            val a = points[k - 1]; val b = points[k]; val f = (tick - ticks[k - 1]) / (ticks[k] - ticks[k - 1]).coerceAtLeast(1)
            return Vec3(a.x + (b.x - a.x) * f, a.y + (b.y - a.y) * f, a.z + (b.z - a.z) * f)
        }
    }

    companion object {
        const val UNIT = 0.0254f
        const val GRAVITY = 320f * UNIT
        const val TICK = 64f
        /** Round time after freeze time, and the bomb's fuse; plain constants so tools built without Android can use them. */
        const val ROUND_SECONDS = 115f; const val BOMB_SECONDS = 40f
        const val ALIVE = 1; const val DUCK = 2; const val AIR = 4; const val SCOPED = 8; const val WALK = 16; const val FLASHED = 32; const val BUSY = 64; const val PRESENT = 128
        const val HELMET = 1; const val KIT = 2; const val HAS_BOMB = 4
        const val G_SMOKE = 1; const val G_HE = 2; const val G_MOLOTOV = 4; const val G_INCENDIARY = 8; const val G_DECOY = 64

        private fun display(x: Float, y: Float, z: Float) = Vec3(x * UNIT, z * UNIT, -y * UNIT)

        fun read(source: InputStream): Replay = DataInputStream(GZIPInputStream(source, 1 shl 16).buffered(1 shl 16)).use { s ->
            val magic = ByteArray(4); s.readFully(magic)
            val version = when (String(magic)) { "NAR1" -> 1; "NAR2" -> 2; else -> 0 }
            require(version > 0) { "不是可识别的录像文件" }
            fun str(): String { val b = ByteArray(s.readUnsignedShort()); s.readFully(b); return String(b, Charsets.UTF_8) }
            fun vec() = display(s.readFloat(), s.readFloat(), s.readFloat())
            val map = str(); val rate = s.readFloat()
            require(rate.isFinite() && rate in 8f..256f) { "录像的 tick 率不对" }
            val players = List(s.readUnsignedByte()) { str().also { s.readLong() } }
            val slots = players.size
            val rounds = ArrayList<Round>()
            repeat(s.readUnsignedShort()) { index ->
                val start = s.readInt(); val freeze = s.readInt(); val end = s.readInt()
                val winner = s.readUnsignedByte(); val reason = s.readUnsignedByte()
                var ct = s.readUnsignedByte(); var t = s.readUnsignedByte()
                // The first converter counted the round that had just ended twice.
                if (version == 1) { if (winner == 3 && ct > 0) ct--; if (winner == 2 && t > 0) t-- }
                val nameCT = if (version >= 2) str() else ""; val nameT = if (version >= 2) str() else ""
                val team = IntArray(slots); val before = IntArray(slots * 3)
                repeat(s.readUnsignedByte()) {
                    val slot = s.readUnsignedByte(); val side = s.readUnsignedByte(); if (slot < slots) team[slot] = side
                    if (version >= 2) for (k in 0..2) { val v = s.readUnsignedByte(); if (slot < slots) before[slot * 3 + k] = v }
                }
                val n = s.readInt(); require(n in 0..2_000_000)
                val ticks = IntArray(n); val size = n * slots
                val x = FloatArray(size); val y = FloatArray(size); val z = FloatArray(size); val yaw = FloatArray(size)
                val pitch = ByteArray(size); val health = ByteArray(size); val flags = ByteArray(size); val weapon = ByteArray(size)
                val armor = ByteArray(size); val gear = ByteArray(size); val money = ShortArray(size); val clip = ByteArray(size)
                val zoom = ByteArray(size); val grenades = ByteArray(size); val primary = ByteArray(size); val pistol = ByteArray(size)
                val extra = ByteArray(9)
                for (i in 0 until n) {
                    ticks[i] = s.readInt()
                    repeat(s.readUnsignedByte()) {
                        val slot = s.readUnsignedByte()
                        val sx = s.readShort() / 8f; val sy = s.readShort() / 8f; val sz = s.readShort() / 8f
                        val angle = s.readUnsignedShort() * 360f / 65536f
                        val p = s.readByte(); val hp = s.readByte(); val fl = s.readUnsignedByte(); val w = s.readByte()
                        if (version >= 2) s.readFully(extra)
                        if (slot < slots) {
                            val o = i * slots + slot
                            x[o] = sx * UNIT; y[o] = sz * UNIT; z[o] = -sy * UNIT; yaw[o] = angle
                            pitch[o] = p; health[o] = hp; flags[o] = (fl or PRESENT).toByte(); weapon[o] = w
                            if (version >= 2) {
                                armor[o] = extra[0]; gear[o] = extra[1]
                                money[o] = (((extra[2].toInt() and 255) shl 8) or (extra[3].toInt() and 255)).toShort()
                                clip[o] = extra[4]; zoom[o] = extra[5]; grenades[o] = extra[6]; primary[o] = extra[7]; pistol[o] = extra[8]
                            }
                        }
                    }
                }
                val nades = ArrayList<Nade>()
                repeat(s.readUnsignedShort()) {
                    val kind = s.readUnsignedByte(); val thrower = s.readByte().toInt(); val fl = s.readUnsignedByte()
                    val eye = vec(); val nyaw = s.readFloat(); val npitch = s.readFloat()
                    val fxStart = s.readInt(); val fxEnd = s.readInt(); val fx = vec()
                    val count = s.readUnsignedShort()
                    val nt = IntArray(count); val np = Array(count) { i -> nt[i] = s.readInt(); vec() }
                    val fires = Array(s.readUnsignedByte()) { vec() }
                    // The last recorded point is stamped when the grenade's entity went away, which for a smoke is when the
                    // smoke cleared and for the others can be seconds after they went off. It reached that point when its
                    // effect began; flying it there over the longer time would bend its last stretch through walls.
                    if (count >= 2 && fxStart > nt[count - 2] && fxStart < nt[count - 1]) nt[count - 1] = fxStart
                    if (count >= 2) nades.add(Nade(kind, thrower, fl, eye, nyaw, npitch, fxStart, fxEnd, fx, nt, np, fires))
                }
                val kills = List(s.readUnsignedShort()) {
                    val tick = s.readInt(); val killer = s.readByte().toInt(); val victim = s.readByte().toInt()
                    val assister = if (version >= 2) s.readByte().toInt() else -1
                    val w = s.readUnsignedByte(); val fl = s.readUnsignedByte()
                    Kill(tick, killer, victim, assister, w, fl)
                }
                val shotCount = s.readInt(); require(shotCount in 0..1_000_000)
                val shots = IntArray(shotCount) { s.readInt() }
                val bomb = List(s.readUnsignedByte()) { Bomb(s.readInt(), s.readUnsignedByte(), vec()) }
                if (n > 0) rounds.add(Round(index, start, freeze, end.coerceAtLeast(ticks[n - 1]), winner, ct, t, nameCT, nameT, team, before, ticks, x, y, z, yaw, pitch, health, flags, weapon,
                    armor, gear, money, clip, zoom, grenades, primary, pistol, nades, kills, shots, bomb, rate).also { it.reason = reason })
            }
            require(rounds.isNotEmpty()) { "录像里没有回合" }
            // Voice, if the converter found any, follows the rounds; older files end here.
            val voice = runCatching {
                val tag = ByteArray(4); s.readFully(tag)
                if (String(tag) != "VOX1") return@runCatching Voice.NONE
                val n = s.readInt(); require(n in 0..4_000_000)
                val ticks = IntArray(n); val who = ByteArray(n)
                val packets = Array(n) { i -> ticks[i] = s.readInt(); who[i] = s.readByte(); ByteArray(s.readUnsignedShort()).also { s.readFully(it) } }
                Voice(ticks, who, packets)
            }.getOrDefault(Voice.NONE)
            // Then where each shot went, per round in file order (rounds without samples were left out above).
            runCatching {
                val tag = ByteArray(4); s.readFully(tag)
                if (String(tag) != "PUN1") return@runCatching
                val byIndex = rounds.associateBy { it.index }
                repeat(s.readUnsignedShort()) { index ->
                    val n = s.readInt(); require(n in 0..1_000_000)
                    val a = FloatArray(n * 2) { s.readFloat() }
                    byIndex[index]?.let { r -> if (r.shots.size == n) r.aims = a }
                }
            }
            // Then what was let go of, per round in file order.
            runCatching {
                val tag = ByteArray(4); s.readFully(tag)
                if (String(tag) != "DRP1") return@runCatching
                val byIndex = rounds.associateBy { it.index }
                repeat(s.readUnsignedShort()) { index ->
                    val list = List(s.readUnsignedShort()) {
                        val code = s.readUnsignedByte(); val from = s.readByte().toInt(); val to = s.readByte().toInt()
                        val start = s.readInt(); val end = s.readInt()
                        val n = s.readUnsignedByte(); val t = IntArray(n)
                        val pts = Array(n) { i -> t[i] = s.readInt(); vec() }
                        Loose(code, from, to, start, end, t, pts)
                    }.filter { it.ticks.isNotEmpty() }
                    byIndex[index]?.loose = list
                }
            }
            Replay(map, rate, players, rounds, voice)
        }

        fun kindName(kind: Int) = when (kind) { 0 -> "烟雾"; 1 -> "闪光"; 2 -> "高爆"; 3 -> "燃烧"; else -> "诱饵" }

        /** One-byte weapon code from the converter to a short name. */
        fun weaponName(code: Int) = when (code) {
            1 -> "P2000"; 2 -> "Glock"; 3 -> "P250"; 4 -> "Deagle"; 5 -> "Five-SeveN"; 6 -> "双枪"; 7 -> "Tec-9"; 8 -> "CZ75"; 9 -> "USP"; 10 -> "R8"
            21 -> "MP7"; 22 -> "MP9"; 23 -> "野牛"; 24 -> "MAC-10"; 25 -> "UMP"; 26 -> "P90"; 27 -> "MP5"
            41 -> "截短"; 42 -> "Nova"; 43 -> "MAG-7"; 44 -> "XM1014"; 45 -> "M249"; 46 -> "Negev"
            61 -> "Galil"; 62 -> "FAMAS"; 63 -> "AK-47"; 64 -> "M4A4"; 65 -> "M4A1-S"; 66 -> "SSG08"; 67 -> "SG553"; 68 -> "AUG"; 69 -> "AWP"; 70 -> "SCAR-20"; 71 -> "G3SG1"
            81 -> "电击枪"; 84 -> "C4"; 85 -> "刀"; 87 -> "环境"
            111 -> "诱饵"; 112, 113 -> "火"; 114 -> "闪光"; 115 -> "烟"; 116 -> "雷"
            else -> ""
        }
    }
}
