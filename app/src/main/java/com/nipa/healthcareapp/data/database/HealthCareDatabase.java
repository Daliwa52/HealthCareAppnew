package com.nipa.healthcareapp.data.database;

import android.content.Context;
import androidx.room.Database;
import androidx.room.Room;
import androidx.room.RoomDatabase;
import androidx.room.TypeConverters;
import com.nipa.healthcareapp.data.models.Notification; // Assuming this is the Java class
import com.nipa.healthcareapp.data.models.ClientHistoryItem; // Assuming this is the Java class
// Converters is assumed to be the Java class com.nipa.healthcareapp.data.database.Converters

@Database(
    entities = {Notification.class, ClientHistoryItem.class},
    version = 1,
    exportSchema = false
)
@TypeConverters(Converters.class) // Assuming Converters.java is in the same package
public abstract class HealthCareDatabase extends RoomDatabase {

    public abstract NotificationDao notificationDao(); // Assuming NotificationDao.java
    public abstract ClientHistoryDao clientHistoryDao(); // Assuming ClientHistoryDao.java

    private static volatile HealthCareDatabase INSTANCE;

    public static HealthCareDatabase getDatabase(final Context context) {
        if (INSTANCE == null) {
            synchronized (HealthCareDatabase.class) { // Use the class object for lock
                if (INSTANCE == null) {
                    INSTANCE = Room.databaseBuilder(
                        context.getApplicationContext(),
                        HealthCareDatabase.class,
                        "healthcare_database"
                    )
                    .fallbackToDestructiveMigration()
                    // .addCallback(sRoomDatabaseCallback) // Optional: if you have a callback
                    .build();
                }
            }
        }
        return INSTANCE;
    }

    // Optional: If you need a callback, for example, to pre-populate data
    // private static RoomDatabase.Callback sRoomDatabaseCallback = new RoomDatabase.Callback() {
    //     @Override
    //     public void onCreate(@NonNull SupportSQLiteDatabase db) {
    //         super.onCreate(db);
    //         // If you want to keep data through app restarts,
    //         // comment out the following block
    //         // Executors.newSingleThreadScheduledExecutor().execute(() -> {
    //         //    getDatabase(context).yourDao().deleteAll(); // Example
    //         //    YourData data = new YourData(...); // Example
    //         //    getDatabase(context).yourDao().insert(data); // Example
    //         // });
    //     }
    // };
}
