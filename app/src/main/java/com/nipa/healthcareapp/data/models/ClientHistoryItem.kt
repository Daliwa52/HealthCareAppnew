package com.nipa.healthcareapp.data.models

import androidx.room.Entity
import androidx.room.PrimaryKey
import androidx.room.TypeConverters
import java.time.LocalDate
import java.util.UUID

enum class ConsultationType {
    IN_PERSON,
    ONLINE,
    PHONE_CALL,
    OTHER
}

@Entity(tableName = "client_history_item")
data class ClientHistoryItem(
    @PrimaryKey
    val id: String = UUID.randomUUID().toString(),
    val providerId: String,
    val patientId: String,
    val patientName: String,
    val consultationDate: LocalDate,
    val consultationType: ConsultationType,
    val notes: String = "",
    val attachments: List<String> = emptyList(),
    var synced: Boolean = true
) {
    companion object {
        fun validate(item: ClientHistoryItem): List<String> {
            val errors = mutableListOf<String>()
            
            if (item.id.isEmpty()) errors.add("ID is required")
            if (item.providerId.isEmpty()) errors.add("Provider ID is required")
            if (item.patientId.isEmpty()) errors.add("Patient ID is required")
            if (item.patientName.isEmpty()) errors.add("Patient name is required")
            // LocalDate doesn't have isEmpty, check if it's before a reasonable date
            if (item.consultationDate.isBefore(LocalDate.now().minusYears(100))) {
                errors.add("Consultation date is too old")
            }
            // ConsultationType is an enum, so it can't be empty
            
            if (item.attachments.size > 10) {
                errors.add("Maximum 10 attachments allowed")
            }
            
            return errors
        }
    }
}
