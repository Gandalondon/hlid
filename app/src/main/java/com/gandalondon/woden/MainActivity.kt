package com.gandalondon.woden

import android.Manifest
import android.annotation.SuppressLint
import android.app.Activity
import android.content.ContentValues
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Color
import android.hardware.GeomagneticField
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.os.Build
import android.os.Bundle
import android.os.Environment
import android.os.Handler
import android.os.Looper
import android.os.VibrationEffect
import android.os.Vibrator
import android.provider.MediaStore
import android.util.Base64
import android.view.WindowInsets
import android.view.WindowInsetsController
import android.view.WindowManager
import android.webkit.JavascriptInterface
import android.webkit.WebView
import android.widget.FrameLayout

// Woden test build: app C in a WebView, plus a small native bridge for the Cannon Hill Common test walk:
// real GPS (TrackService), compass heading, a GPX trace in Downloads/Woden, pictures to Photos, keep-awake and a buzz.
// Like Sniff and Relay, the WebView is padded by the status and gesture bars, so the page lays out between them.
class MainActivity : Activity(), SensorEventListener {
    private lateinit var web: WebView
    private val main = Handler(Looper.getMainLooper())
    private var sensors: SensorManager? = null
    private var heading = Float.NaN
    private var lastSent = Float.NaN
    private var declination = 0f
    private var pendingGps = false
    private var upright = false

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.statusBarColor = Color.TRANSPARENT
        window.navigationBarColor = Color.TRANSPARENT
        window.decorView.setBackgroundColor(Color.WHITE)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            window.setDecorFitsSystemWindows(false)
            window.insetsController?.setSystemBarsAppearance(
                WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS or WindowInsetsController.APPEARANCE_LIGHT_NAVIGATION_BARS,
                WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS or WindowInsetsController.APPEARANCE_LIGHT_NAVIGATION_BARS
            )
        }
        val root = FrameLayout(this)
        root.setBackgroundColor(Color.WHITE)
        web = WebView(this)
        web.setBackgroundColor(Color.WHITE)
        web.settings.javaScriptEnabled = true
        web.settings.domStorageEnabled = true
        web.isVerticalScrollBarEnabled = false
        web.overScrollMode = WebView.OVER_SCROLL_NEVER
        web.addJavascriptInterface(Bridge(), "WodenNative")
        root.addView(web, FrameLayout.LayoutParams(FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.MATCH_PARENT))
        root.setOnApplyWindowInsetsListener { v, insets ->
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                val sys = insets.getInsets(WindowInsets.Type.systemBars() or WindowInsets.Type.displayCutout())
                v.setPadding(sys.left, sys.top, sys.right, sys.bottom)
            } else {
                @Suppress("DEPRECATION")
                v.setPadding(insets.systemWindowInsetLeft, insets.systemWindowInsetTop, insets.systemWindowInsetRight, insets.systemWindowInsetBottom)
            }
            insets
        }
        setContentView(root)
        root.requestApplyInsets()
        sensors = getSystemService(SENSOR_SERVICE) as SensorManager
        TrackService.listener = { lat, lon, acc, t ->
            main.post {
                declination = GeomagneticField(lat.toFloat(), lon.toFloat(), 0f, t).declination
                js("window.wodenFix&&wodenFix($lat,$lon,$acc,$t)")
            }
        }
        web.loadUrl("file:///android_asset/index.html")
    }

    private fun js(code: String) = web.evaluateJavascript(code, null)

    private fun hasLocation() = checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED

    private fun startGps() {
        val i = Intent(this, TrackService::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) startForegroundService(i) else startService(i)
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == 1) {
            val ok = hasLocation()
            js("window.wodenPerm&&wodenPerm($ok)")
            if (ok && pendingGps) { pendingGps = false; startGps() }
        }
    }

    @Suppress("DEPRECATION")
    override fun onBackPressed() {
        web.evaluateJavascript("(window.wodenBack&&wodenBack())?1:0") { r -> if (r != "1") super.onBackPressed() }
    }

    override fun onDestroy() {
        sensors?.unregisterListener(this)
        TrackService.listener = null
        super.onDestroy()
    }

    // compass: rotation vector -> azimuth (true north), sent when it moves by a degree or more
    override fun onSensorChanged(e: SensorEvent) {
        val r = FloatArray(9); val o = FloatArray(3)
        SensorManager.getRotationMatrixFromVector(r, e.values)
        // flat-ish: the top of the screen is the way you face. Held up steeply: use the way the back of the phone
        // points instead (the flat maths goes unstable near upright). Hysteresis so it doesn't flip between the two.
        SensorManager.getOrientation(r, o)
        val pitch = Math.toDegrees(o[1].toDouble())
        upright = if (upright) pitch < -45 else pitch < -60
        if (upright) {
            val out = FloatArray(9)
            SensorManager.remapCoordinateSystem(r, SensorManager.AXIS_X, SensorManager.AXIS_Z, out)
            SensorManager.getOrientation(out, o)
        }
        var deg = Math.toDegrees(o[0].toDouble()).toFloat() + declination
        deg = (deg + 360f) % 360f
        heading = if (heading.isNaN()) deg else {
            var d = deg - heading; if (d > 180) d -= 360f; if (d < -180) d += 360f
            (heading + d * 0.25f + 360f) % 360f
        }
        var diff = if (lastSent.isNaN()) 999f else Math.abs(heading - lastSent)
        if (diff > 180) diff = 360 - diff
        if (diff >= 1f) { lastSent = heading; js("window.wodenHeading&&wodenHeading(${String.format(java.util.Locale.US, "%.1f", heading)})") }
    }

    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}

    inner class Bridge {
        @JavascriptInterface fun hasLocation(): Boolean = this@MainActivity.hasLocation()

        @JavascriptInterface fun requestLocation() = main.post {
            if (hasLocation()) js("window.wodenPerm&&wodenPerm(true)")
            else {
                val p = mutableListOf(Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION)
                if (Build.VERSION.SDK_INT >= 33) p.add(Manifest.permission.POST_NOTIFICATIONS)
                requestPermissions(p.toTypedArray(), 1)
            }
        }

        @JavascriptInterface fun startGps() = main.post {
            if (hasLocation()) this@MainActivity.startGps() else { pendingGps = true; requestLocation() }
        }

        @JavascriptInterface fun stopGps() = main.post {
            if (!TrackService.recording) stopService(Intent(this@MainActivity, TrackService::class.java))
        }

        @JavascriptInterface fun startTrace(name: String) = main.post { TrackService.startTrace(name) }

        // writes the GPX to Downloads/Woden and returns where it went ("" if nothing was recorded)
        @JavascriptInterface fun endTrace(): String {
            val where = TrackService.endTrace(this@MainActivity)
            main.post { stopService(Intent(this@MainActivity, TrackService::class.java)) }
            return where
        }

        @JavascriptInterface fun startCompass() = main.post {
            val s = sensors?.getDefaultSensor(Sensor.TYPE_ROTATION_VECTOR) ?: return@post
            sensors?.registerListener(this@MainActivity, s, SensorManager.SENSOR_DELAY_UI)
        }

        @JavascriptInterface fun stopCompass() = main.post { sensors?.unregisterListener(this@MainActivity) }

        @JavascriptInterface fun keepAwake(on: Boolean) = main.post {
            if (on) window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
            else window.clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        }

        @JavascriptInterface fun vibrate(ms: Int) {
            val v = getSystemService(VIBRATOR_SERVICE) as Vibrator
            v.vibrate(VibrationEffect.createOneShot(ms.toLong(), VibrationEffect.DEFAULT_AMPLITUDE))
        }

        // a PNG (base64, no data: prefix) into Photos, in Pictures/Woden
        @JavascriptInterface fun savePng(b64: String, name: String): Boolean = try {
            val bytes = Base64.decode(b64, Base64.DEFAULT)
            val cv = ContentValues().apply {
                put(MediaStore.Images.Media.DISPLAY_NAME, "$name.png")
                put(MediaStore.Images.Media.MIME_TYPE, "image/png")
                put(MediaStore.Images.Media.RELATIVE_PATH, Environment.DIRECTORY_PICTURES + "/Woden")
            }
            val uri = contentResolver.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, cv)!!
            contentResolver.openOutputStream(uri)!!.use { it.write(bytes) }
            true
        } catch (e: Exception) { false }
    }
}
