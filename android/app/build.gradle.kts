plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "de.doppelcheck.app"
    compileSdk = 34

    defaultConfig {
        applicationId = "de.doppelcheck.app"
        minSdk = 29                 // Android 10
        targetSdk = 34
        versionCode = 1
        versionName = "0.1"
    }

    buildTypes {
        release {
            // No signing config here on purpose: keys must never be committed.
            // Debug builds are signed with the local debug keystore automatically.
            isMinifyEnabled = false
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = "17"
    }
    buildFeatures {
        compose = true
    }
    composeOptions {
        kotlinCompilerExtensionVersion = "1.5.14"
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.activity:activity-compose:1.9.0")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.8.2")
    implementation("androidx.lifecycle:lifecycle-viewmodel-ktx:2.8.2")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.2")

    val composeBom = platform("androidx.compose:compose-bom:2024.06.00")
    implementation(composeBom)
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.material3:material3")
    debugImplementation("androidx.compose.ui:ui-tooling")
    implementation("androidx.compose.ui:ui-tooling-preview")

    // OkHttp is pinned ON PURPOSE. Retrofit 2.11.0 declares okhttp 3.14.9, which is the
    // Java-only release: it has no Kotlin companion extensions (toMediaTypeOrNull,
    // toRequestBody) and is out of maintenance. The BOM lifts the whole OkHttp/Okio
    // group to 4.12.0 (Kotlin, requires Android 5.0 / API 21 – we target minSdk 29).
    implementation(platform("com.squareup.okhttp3:okhttp-bom:4.12.0"))
    implementation("com.squareup.okhttp3:okhttp")

    implementation("com.squareup.retrofit2:retrofit:2.11.0")
    implementation("com.squareup.retrofit2:converter-gson:2.11.0")
}

/**
 * Prints the OkHttp/Okio versions that actually end up on the runtime classpath:
 *     ./gradlew :app:okhttpVersion
 * Use this to confirm the pin above took effect instead of guessing.
 */
tasks.register("okhttpVersion") {
    group = "verification"
    description = "Prints the resolved OkHttp and Okio versions (debug runtime classpath)."
    doLast {
        configurations.getByName("debugRuntimeClasspath")
            .resolvedConfiguration.resolvedArtifacts
            .map { it.moduleVersion.id }
            .filter { it.group == "com.squareup.okhttp3" || it.group == "com.squareup.okio" }
            .distinctBy { "${it.group}:${it.name}" }
            .sortedBy { it.name }
            .forEach { println("${it.group}:${it.name}:${it.version}") }
    }
}
