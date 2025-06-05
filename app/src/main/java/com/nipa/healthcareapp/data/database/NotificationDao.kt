package com.nipa.healthcareapp.data.database

import androidx.room.*
import com.nipa.healthcareapp.data.models.Notification
import kotlinx.coroutines.flow.Flow

@Dao
interface NotificationDao {
    @Query("SELECT * FROM notification WHERE userId = :userId ORDER BY timestamp DESC")
    fun getNotifications(userId: String): Flow<List<Notification>>
    
    @Query("SELECT * FROM notification")
    suspend fun getAll(): List<Notification>
    
    @Query("SELECT * FROM notification WHERE synced = 0")
    suspend fun getUnsynced(): List<Notification>
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(notification: Notification)
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(notifications: List<Notification>)

    @Update
    suspend fun update(notification: Notification)

    @Query("DELETE FROM notification WHERE userId = :userId")
    suspend fun deleteAll(userId: String)
    
    @Query("DELETE FROM notification WHERE id IN (:ids)")
    suspend fun deleteByIds(ids: List<String>)

    @Query("SELECT COUNT(*) FROM notification WHERE userId = :userId AND read = 0")
    suspend fun getUnreadCount(userId: String): Int
}
