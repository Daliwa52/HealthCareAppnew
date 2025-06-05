package com.nipa.healthcareapp.data.database;

import androidx.room.TypeConverter;
import com.google.firebase.Timestamp;
import com.nipa.healthcareapp.data.models.ConsultationType; // Assuming this is the Java enum
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.stream.Collectors;

public class Converters {

    // Firebase Timestamp converters
    @TypeConverter
    public Long fromTimestamp(Timestamp timestamp) {
        return timestamp == null ? null : timestamp.getSeconds();
    }

    @TypeConverter
    public Timestamp toTimestamp(Long seconds) {
        return seconds == null ? null : new Timestamp(seconds, 0);
    }

    // LocalDate converters
    private static final DateTimeFormatter dateFormatter = DateTimeFormatter.ISO_LOCAL_DATE;

    @TypeConverter
    public String fromLocalDate(LocalDate localDate) {
        return localDate == null ? null : localDate.format(dateFormatter);
    }

    @TypeConverter
    public LocalDate toLocalDate(String dateString) {
        return dateString == null ? null : LocalDate.parse(dateString, dateFormatter);
    }

    // ConsultationType enum converters
    @TypeConverter
    public String fromConsultationType(ConsultationType type) {
        return type == null ? null : type.name();
    }

    @TypeConverter
    public ConsultationType toConsultationType(String typeName) {
        return typeName == null ? null : ConsultationType.valueOf(typeName);
    }

    // List<String> converters
    @TypeConverter
    public String fromStringList(List<String> list) {
        if (list == null) {
            return null;
        }
        // Using String.join as a more direct equivalent to joinToString
        return String.join(",", list);
    }

    @TypeConverter
    public List<String> toStringList(String listString) {
        if (listString == null || listString.isEmpty()) { // Also handle empty string to avoid [""]
            return Collections.emptyList();
        }
        // filter { it.isNotEmpty() } equivalent
        // The original Kotlin filter { it.isNotEmpty() } would remove empty strings resulting from, e.g., ",,"
        // String.split behaves differently with trailing empty strings depending on the limit.
        // The stream approach handles this well.
        return Arrays.stream(listString.split(",", -1)) // Use -1 limit to include trailing empty strings for filtering
                     .filter(s -> !s.isEmpty())
                     .collect(Collectors.toList());
    }
}
