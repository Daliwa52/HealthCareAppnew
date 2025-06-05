package com.nipa.healthcareapp

import java.time.LocalDate

data class ClientHistoryItem(
    val patientName: String,
    val consultationType: ConsultationType,
    val consultationDate: LocalDate,
    val notes: String
)

enum class ConsultationType {
    GENERAL_CHECKUP,
    SPECIALIST,
    EMERGENCY,
    FOLLOW_UP
}
