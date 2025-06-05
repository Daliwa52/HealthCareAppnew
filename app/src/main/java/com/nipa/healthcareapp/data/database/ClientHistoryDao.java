package com.nipa.healthcareapp.data.database;

import androidx.lifecycle.LiveData; // For Flow replacement
import androidx.room.Dao;
import androidx.room.Delete;
import androidx.room.Insert;
import androidx.room.OnConflictStrategy;
import androidx.room.Query;
import androidx.room.Update;
import com.nipa.healthcareapp.data.models.ClientHistoryItem; // Assuming this is the Java class
import java.util.List;

@Dao
public interface ClientHistoryDao {

    @Query("SELECT * FROM client_history_item WHERE providerId = :providerId ORDER BY consultationDate DESC")
    LiveData<List<ClientHistoryItem>> getClientHistory(String providerId);

    @Query("SELECT * FROM client_history_item WHERE patientId = :patientId ORDER BY consultationDate DESC")
    LiveData<List<ClientHistoryItem>> getPatientHistory(String patientId);

    @Query("SELECT * FROM client_history_item")
    List<ClientHistoryItem> getAll(); // Was suspend, now direct blocking call

    @Query("SELECT * FROM client_history_item WHERE synced = 0")
    List<ClientHistoryItem> getUnsynced(); // Was suspend, now direct blocking call

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    void insert(ClientHistoryItem item); // Was suspend, now direct blocking call

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    void insertAll(List<ClientHistoryItem> items); // Was suspend, now direct blocking call

    @Update
    void update(ClientHistoryItem item); // Was suspend, now direct blocking call

    @Delete
    void delete(ClientHistoryItem item); // Was suspend, now direct blocking call

    @Query("DELETE FROM client_history_item WHERE id IN (:ids)")
    void deleteByIds(List<String> ids); // Was suspend, now direct blocking call

    @Query("SELECT COUNT(*) FROM client_history_item WHERE providerId = :providerId")
    int getHistoryCount(String providerId); // Was suspend, now direct blocking call
}
