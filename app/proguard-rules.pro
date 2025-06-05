# Add project specific ProGuard rules here.
# You can control the set of applied configuration files using the
# proguardFiles setting in build.gradle.
#
# For more details, see
#   http://developer.android.com/guide/developing/tools/proguard.html

# Keep Firebase classes
-keep class com.google.firebase.** { *; }
-keep class com.google.android.gms.** { *; }
-keep class com.google.firebase.messaging.FirebaseMessagingService { *; }
-keep class com.google.firebase.iid.FirebaseInstanceIdService { *; }

# Keep Kotlin metadata
-keepattributes RuntimeVisibleAnnotations
-keepattributes RuntimeVisibleParameterAnnotations
-keepattributes RuntimeVisibleTypeAnnotations
-keepattributes Signature

# Keep coroutines
-keepnames class kotlin.coroutines.jvm.internal.BaseContinuationImpl
-keepclassmembers class kotlin.coroutines.jvm.internal.BaseContinuationImpl {
    Object result;
    Throwable exception;
}

# Keep Room database
-keep class * extends androidx.room.RoomDatabase { *; }
-keep class * implements androidx.room.DatabaseConfiguration { *; }
-keep class * implements androidx.room.InvalidationTracker { *; }
-keep class * implements androidx.room.RoomDatabase$Callback { *; }

# Keep navigation components
-keep class androidx.navigation.** { *; }
-keep class androidx.navigation.dynamicfeatures.** { *; }

# Keep Retrofit
-keep class retrofit2.** { *; }
-keepattributes Signature
-keepattributes Exceptions

# Keep Coroutines
-keepattributes kotlinx.coroutines.*
-keepattributes kotlinx.coroutines.flow.*

# Keep Material Design components
-keep class com.google.android.material.** { *; }

# Keep ViewModel
-keep class androidx.lifecycle.** { *; }
-keepclassmembers class * implements androidx.lifecycle.ViewModel {
    <init>(...);
}

# Keep ViewModelFactory
-keep class * extends androidx.lifecycle.ViewModelProvider$Factory { *; }

# Keep ViewBinding
-keepclassmembers class * {
    @androidx.databinding.BindingAdapter <methods>;
}

# Keep Compose
-keep class androidx.compose.** { *; }
-keepclassmembers class androidx.compose.** { *; }

# Keep data classes
-keepclassmembers class * {
    @com.google.firebase.annotations.KeepForSdk <fields>;
}

# Keep enums
-keepclassmembers enum * {
    public static **[] values();
    public static ** valueOf(java.lang.String);
}

# Keep annotations
-keepattributes *Annotation*
-keepattributes InnerClasses
-keepattributes EnclosingMethod
-keepattributes Exceptions
-keepattributes Signature
-keepattributes SourceFile,LineNumberTable
-keepattributes RuntimeVisibleAnnotations,RuntimeVisibleParameterAnnotations,RuntimeVisibleTypeAnnotations
-keepattributes RuntimeInvisibleAnnotations,RuntimeInvisibleParameterAnnotations,RuntimeInvisibleTypeAnnotations
-keepattributes *Annotation*
-keepattributes *Parameters*
-keepattributes *Signature*
-keepattributes *Exceptions*
-keepattributes *SourceFile*
-keepattributes *LineNumberTable*
-keepattributes *InnerClasses*
-keepattributes *EnclosingMethod*
-keepattributes *RuntimeVisibleAnnotations*
-keepattributes *RuntimeVisibleParameterAnnotations*
-keepattributes *RuntimeVisibleTypeAnnotations*
-keepattributes *RuntimeInvisibleAnnotations*
-keepattributes *RuntimeInvisibleParameterAnnotations*
-keepattributes *RuntimeInvisibleTypeAnnotations*
-keepattributes *Deprecated*
-keepattributes *Synthetic*
-keepattributes *AnnotationDefault*
-keepattributes *Signature*
-keepattributes *Exceptions*
-keepattributes *SourceFile*
-keepattributes *LineNumberTable*
-keepattributes *InnerClasses*
-keepattributes *EnclosingMethod*