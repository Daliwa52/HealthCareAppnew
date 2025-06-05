plugins {
    alias(libs.plugins.android.application)
    // alias(libs.plugins.kotlin.android) // Removed
    // id("kotlin-kapt") // Removed
    id("com.google.gms.google-services")
    // id("org.jetbrains.kotlin.plugin.serialization") version "1.9.22" // Removed
}

android {
    namespace = "com.nipa.healthcareapp"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.nipa.healthcareapp"
        minSdk = 21
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    signingConfigs {
        create("release") {
            storeFile = file("release-key.jks")
            storePassword = "your-keystore-password"
            keyAlias = "release-key"
            keyPassword = "your-key-password"
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
            signingConfig = signingConfigs.getByName("release")
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    // kotlinOptions { // Removed
    //     jvmTarget = "17"
    //     // Additional options for Java 23 compatibility
    //     freeCompilerArgs = listOf("-Xjvm-default=all")
    // }
    buildFeatures {
        viewBinding = true
    }
}

dependencies {
    // Core Android dependencies
    implementation("androidx.core:core:1.12.0") // Changed from core-ktx
    implementation("androidx.appcompat:appcompat:1.6.1")
    implementation("com.google.android.material:material:1.11.0")
    implementation("androidx.constraintlayout:constraintlayout:2.1.4")

    // Lifecycle components
    // implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.7.0") // Removed
    // implementation("androidx.lifecycle:lifecycle-viewmodel-ktx:2.7.0") // Removed
    // implementation("androidx.lifecycle:lifecycle-livedata-ktx:2.7.0") // Removed
    implementation("androidx.lifecycle:lifecycle-common-java8:2.7.0")

    // Serialization
    // implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.6.2") // Removed
    // implementation("org.jetbrains.kotlinx:kotlinx-serialization-protobuf:1.6.2") // Removed

    // DataStore and Room
    implementation("androidx.datastore:datastore-preferences:1.0.0")
    implementation("androidx.room:room-runtime:2.6.1")
    // implementation("androidx.room:room-ktx:2.6.1") // Removed
    annotationProcessor("androidx.room:room-compiler:2.6.1") // Changed from kapt

    // Firebase
    implementation(platform("com.google.firebase:firebase-bom:32.8.0"))
    implementation("com.google.firebase:firebase-analytics") // Changed from -ktx
    implementation("com.google.firebase:firebase-auth") // Changed from -ktx
    implementation("com.google.firebase:firebase-firestore") // Changed from -ktx
    implementation("com.google.firebase:firebase-crashlytics") // Changed from -ktx
    implementation("com.google.firebase:firebase-perf") // Changed from -ktx
    implementation("com.google.firebase:firebase-storage") // Changed from -ktx
    implementation("com.google.firebase:firebase-messaging") // Changed from -ktx

    // WorkManager
    implementation("androidx.work:work-runtime:2.9.0") // Changed from -ktx
    implementation("androidx.work:work-rxjava3:2.9.0")

    // Paging
    // implementation("androidx.paging:paging-runtime-ktx:3.2.1") // Removed
    implementation("androidx.paging:paging-compose:3.2.1") // Compose specific, kept as per instruction

    // Coroutines
    // implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3") // Removed
    // implementation("org.jetbrains.kotlinx:kotlinx-coroutines-play-services:1.7.3") // Removed

    // Navigation Component
    implementation("androidx.navigation:navigation-fragment:2.7.6") // Changed from -ktx
    implementation("androidx.navigation:navigation-ui:2.7.6") // Changed from -ktx

    // Retrofit
    implementation("com.squareup.retrofit2:retrofit:2.9.0")
    implementation("com.squareup.retrofit2:converter-gson:2.9.0")
    implementation("com.squareup.okhttp3:logging-interceptor:4.12.0")

    // SwipeRefreshLayout, GridLayout, and CircleImageView
    implementation("androidx.swiperefreshlayout:swiperefreshlayout:1.1.0")
    implementation("androidx.gridlayout:gridlayout:1.0.0")
    implementation("de.hdodenhof:circleimageview:3.1.0")

    // Testing
    testImplementation("junit:junit:4.13.2")
    androidTestImplementation("androidx.test.ext:junit:1.1.5")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.5.1")
    androidTestImplementation("androidx.compose.ui:ui-test-junit4:1.5.4") // Compose specific
    debugImplementation("androidx.compose.ui:ui-tooling:1.5.4") // Compose specific
    debugImplementation("androidx.compose.ui:ui-test-manifest:1.5.4") // Compose specific
    // testImplementation("io.mockk:mockk:1.13.8") // Removed
    testImplementation("org.robolectric:robolectric:4.11.1")
}
