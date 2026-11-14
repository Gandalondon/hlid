plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.gandalondon.woden"
    compileSdk = 36

    defaultConfig {
        // The Obtainium APK keeps its own id so it can sit beside the Play install.
        // The Play AAB is built with -PplayId=app.gethlid (the Play Console app).
        applicationId = (findProperty("playId") as String?) ?: "com.gandalondon.woden"
        minSdk = 29
        targetSdk = 36
        versionCode = (System.getenv("GITHUB_RUN_NUMBER") ?: "1").toInt()
        versionName = "0.1.${System.getenv("GITHUB_RUN_NUMBER") ?: "0"}"
    }

    // Same as Rinse: a signing key from CI secrets keeps updates installing over the top.
    // Without the secret each build uses a one-off debug key, so a new build needs uninstall first.
    val ks = System.getenv("SIGNING_KEYSTORE_PATH")
    signingConfigs {
        create("personal") {
            if (ks != null) {
                storeFile = file(ks)
                storePassword = System.getenv("SIGNING_PASSWORD")
                keyAlias = "woden"
                keyPassword = System.getenv("SIGNING_PASSWORD")
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            signingConfig = if (ks != null) signingConfigs.getByName("personal")
            else signingConfigs.getByName("debug")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
}
