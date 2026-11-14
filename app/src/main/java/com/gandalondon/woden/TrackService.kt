package com.gandalondon.woden

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.ContentValues
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.location.Location
import android.location.LocationListener
import android.location.LocationManager
import android.os.Build
import android.os.Bundle
import android.os.Environment
import android.os.IBinder
import android.os.Looper
import android.provider.MediaStore
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.TimeZone

// GPS for the test walk. A foreground service so the trace keeps going with the screen off or the phone in a pocket.
// Fixes go to the page through `listener`; while a trace is on, every fix is kept and written as GPX at the end.
// A copy is saved to app storage every 20 points, so a crash doesn't lose the walk.
class TrackService : Service(), LocationListener {
    companion object {
        var listener: ((Double, Double, Float, Long) -> Unit)? = null
        @Volatile var recording = false
        private val points = mutableListOf<DoubleArray>()   // lat, lon, alt, acc, time
        private var traceName = "Hlid walk"
        private var started = 0L
        private var appDir: File? = null

        fun startTrace(name: String) = synchronized(points) {
            points.clear(); traceName = name; started = System.currentTimeMillis(); recording = true
        }

        fun endTrace(ctx: Context): String = synchronized(points) {
            recording = false
            if (points.isEmpty()) return ""
            val gpx = gpx()
            val stamp = SimpleDateFormat("yyyy-MM-dd-HHmm", Locale.UK).format(Date(started))
            val file = "hlid-$stamp.gpx"
            return try {
                val cv = ContentValues().apply {
                    put(MediaStore.Downloads.DISPLAY_NAME, file)
                    put(MediaStore.Downloads.MIME_TYPE, "application/gpx+xml")
                    put(MediaStore.Downloads.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS + "/Hlid")
                }
                val uri = ctx.contentResolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, cv)!!
                ctx.contentResolver.openOutputStream(uri)!!.use { it.write(gpx.toByteArray()) }
                File(ctx.filesDir, "trace-latest.gpx").writeText(gpx)
                "Downloads/Hlid/$file"
            } catch (e: Exception) {
                File(ctx.filesDir, "trace-latest.gpx").writeText(gpx); ""
            }
        }

        private fun gpx(): String {
            val iso = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'", Locale.UK).apply { timeZone = TimeZone.getTimeZone("UTC") }
            val sb = StringBuilder()
            sb.append("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
            sb.append("<gpx version=\"1.1\" creator=\"Hlid test build\" xmlns=\"http://www.topografix.com/GPX/1/1\">\n")
            sb.append("<trk><name>").append(traceName).append("</name><trkseg>\n")
            for (p in points) {
                sb.append("<trkpt lat=\"%.7f\" lon=\"%.7f\"><ele>%.1f</ele><time>%s</time><hdop>%.1f</hdop></trkpt>\n"
                    .format(Locale.UK, p[0], p[1], p[2], iso.format(Date(p[4].toLong())), p[3] / 5.0))
            }
            sb.append("</trkseg></trk>\n</gpx>\n")
            return sb.toString()
        }
    }

    private var lm: LocationManager? = null

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        appDir = filesDir
        val nm = getSystemService(NotificationManager::class.java)
        nm.createNotificationChannel(NotificationChannel("walk", "Walk tracking", NotificationManager.IMPORTANCE_LOW))
        val open = PendingIntent.getActivity(this, 0, Intent(this, MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP), PendingIntent.FLAG_IMMUTABLE)
        val n = Notification.Builder(this, "walk")
            .setContentTitle("Hlid")
            .setContentText("Following your walk")
            .setSmallIcon(R.drawable.ic_launcher_foreground)
            .setContentIntent(open)
            .setOngoing(true)
            .build()
        if (Build.VERSION.SDK_INT >= 29) startForeground(1, n, ServiceInfo.FOREGROUND_SERVICE_TYPE_LOCATION) else startForeground(1, n)
        lm = getSystemService(LOCATION_SERVICE) as LocationManager
        try {
            lm?.requestLocationUpdates(LocationManager.GPS_PROVIDER, 1000L, 0f, this, Looper.getMainLooper())
            lm?.getLastKnownLocation(LocationManager.GPS_PROVIDER)?.let { if (System.currentTimeMillis() - it.time < 60_000) onLocationChanged(it) }
        } catch (e: SecurityException) { stopSelf() }
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int = START_NOT_STICKY

    override fun onLocationChanged(l: Location) {
        if (recording && l.accuracy <= 50f) synchronized(points) {
            points.add(doubleArrayOf(l.latitude, l.longitude, l.altitude, l.accuracy.toDouble(), l.time.toDouble()))
            if (points.size % 20 == 0) try { File(filesDir, "trace-autosave.gpx").writeText(gpx()) } catch (_: Exception) {}
        }
        listener?.invoke(l.latitude, l.longitude, l.accuracy, l.time)
    }

    @Deprecated("old API") override fun onStatusChanged(p: String?, s: Int, e: Bundle?) {}
    override fun onProviderEnabled(p: String) {}
    override fun onProviderDisabled(p: String) {}

    override fun onDestroy() {
        lm?.removeUpdates(this)
        super.onDestroy()
    }
}
