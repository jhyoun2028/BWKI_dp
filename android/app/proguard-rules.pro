# Retrofit / OkHttp / Gson keep rules (only relevant for release builds with minify enabled)
-keepattributes Signature, InnerClasses, EnclosingMethod, RuntimeVisibleAnnotations
-dontwarn okhttp3.**
-dontwarn okio.**
-dontwarn retrofit2.**

# Data classes are parsed by Gson via reflection
-keep class de.doppelcheck.app.api.** { *; }
