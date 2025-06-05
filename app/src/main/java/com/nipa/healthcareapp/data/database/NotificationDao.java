package com.nipa.healthcareapp.data.database;

import androidx.lifecycle.LiveData;
import androidx.room.Dao;
import androidx.room.Insert;
import androidx.room.OnConflictStrategy;
import androidx.room.Query;
import androidx.room.Update;
import com.nipa.healthcareapp.data.models.Notification; // Assuming this is the Java class
import java.util.List;

@Dao
public interface NotificationDao {

    @Query("SELECT * FROM notification WHERE userId = :userId ORDER BY timestamp DESC")
    LiveData<List<Notification>> getNotifications(String userId);

    @Query("SELECT * FROM notification")
    List<Notification> getAll(); // Was suspend, now direct blocking call

    @Query("SELECT * FROM notification WHERE synced = 0")
    List<Notification> getUnsynced(); // Was suspend, now direct blocking call

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    void insert(Notification notification); // Was suspend, now direct blocking call

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    void insertAll(List<Notification> notifications); // Was suspend, now direct blocking call

    @Update
    void update(Notification notification); // Was suspend, now direct blocking call

    @Query("DELETE FROM notification WHERE userId = :userId")
    void deleteAll(String userId); // Was suspend, now direct blocking call

    @Query("DELETE FROM notification WHERE id IN (:ids)")
    void deleteByIds(List<String> ids); // Was suspend, now direct blocking call

    @Query("SELECT COUNT(*) FROM notification WHERE userId = :userId AND read = 0")
    int getUnreadCount(String userId); // Was suspend, now direct blocking call
}
