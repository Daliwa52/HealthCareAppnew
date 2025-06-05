package com.nipa.healthcareapp.data.database

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.room.TypeConverters
import com.nipa.healthcareapp.data.models.Notification
import com.nipa.healthcareapp.data.models.ClientHistoryItem
import com.nipa.healthcareapp.data.database.Converters

@Database(
    entities = [Notification::class, ClientHistoryItem::class],
    version = 1,
    exportSchema = false
)
@TypeConverters(Converters::class)
abstract class HealthCareDatabase : RoomDatabase() {
    abstract fun notificationDao(): NotificationDao
    abstract fun clientHistoryDao(): ClientHistoryDao

    companion object {
        @Volatile
        private var INSTANCE: HealthCareDatabase? = null

        fun getDatabase(context: Context): HealthCareDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    HealthCareDatabase::class.java,
                    "healthcare_database"
                )
                .fallbackToDestructiveMigration()
                .build()
                INSTANCE = instance
                instance
            }
        }
    }
}
