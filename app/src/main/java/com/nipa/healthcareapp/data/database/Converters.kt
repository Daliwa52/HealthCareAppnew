package com.nipa.healthcareapp.data.database

import androidx.room.TypeConverter
import com.google.firebase.Timestamp
import com.nipa.healthcareapp.data.models.ConsultationType
import java.time.LocalDate
import java.time.format.DateTimeFormatter
import java.util.Date

/**
 * Type converters for Room database
 * Handles conversion of complex types to and from types that Room can persist
 */
class Converters {
    // Firebase Timestamp converters
    @TypeConverter
    fun fromTimestamp(timestamp: Timestamp?): Long? {
        return timestamp?.seconds
    }

    @TypeConverter
    fun toTimestamp(seconds: Long?): Timestamp? {
        return seconds?.let { Timestamp(it, 0) }
    }
    
    // LocalDate converters
    private val dateFormatter = DateTimeFormatter.ISO_LOCAL_DATE
    
    @TypeConverter
    fun fromLocalDate(localDate: LocalDate?): String? {
        return localDate?.format(dateFormatter)
    }
    
    @TypeConverter
    fun toLocalDate(dateString: String?): LocalDate? {
        return dateString?.let { LocalDate.parse(it, dateFormatter) }
    }
    
    // ConsultationType enum converters
    @TypeConverter
    fun fromConsultationType(type: ConsultationType?): String? {
        return type?.name
    }
    
    @TypeConverter
    fun toConsultationType(typeName: String?): ConsultationType? {
        return typeName?.let { ConsultationType.valueOf(it) }
    }
    
    // List<String> converters
    @TypeConverter
    fun fromStringList(list: List<String>?): String? {
        return list?.joinToString(",")
    }
    
    @TypeConverter
    fun toStringList(listString: String?): List<String> {
        return listString?.split(",")?.filter { it.isNotEmpty() } ?: emptyList()
    }
}
