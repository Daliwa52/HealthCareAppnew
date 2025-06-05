package com.nipa.healthcareapp.data.database

import androidx.room.*
import com.nipa.healthcareapp.data.models.ClientHistoryItem
import kotlinx.coroutines.flow.Flow

@Dao
interface ClientHistoryDao {
    @Query("SELECT * FROM client_history_item WHERE providerId = :providerId ORDER BY consultationDate DESC")
    fun getClientHistory(providerId: String): Flow<List<ClientHistoryItem>>

    @Query("SELECT * FROM client_history_item WHERE patientId = :patientId ORDER BY consultationDate DESC")
    fun getPatientHistory(patientId: String): Flow<List<ClientHistoryItem>>
    
    @Query("SELECT * FROM client_history_item")
    suspend fun getAll(): List<ClientHistoryItem>
    
    @Query("SELECT * FROM client_history_item WHERE synced = 0")
    suspend fun getUnsynced(): List<ClientHistoryItem>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(item: ClientHistoryItem)
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(items: List<ClientHistoryItem>)

    @Update
    suspend fun update(item: ClientHistoryItem)

    @Delete
    suspend fun delete(item: ClientHistoryItem)
    
    @Query("DELETE FROM client_history_item WHERE id IN (:ids)")
    suspend fun deleteByIds(ids: List<String>)

    @Query("SELECT COUNT(*) FROM client_history_item WHERE providerId = :providerId")
    suspend fun getHistoryCount(providerId: String): Int
}
