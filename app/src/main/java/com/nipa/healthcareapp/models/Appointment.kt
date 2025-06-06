package com.nipa.healthcareapp.models

import com.google.firebase.Timestamp
import com.google.firebase.firestore.DocumentId
import com.google.firebase.firestore.ServerTimestamp

data class Appointment(
    @DocumentId var id: String? = null, // Firestore document ID
    var patientId: String? = null,
    var patientName: String? = null,
    var professionalId: String? = null,
    var professionalName: String? = null, // Though for provider's view, this might be redundant
    var appointmentTimestamp: Timestamp? = null,
    var reasonForVisit: String? = null,
    var status: String? = null, // e.g., "pending_confirmation", "confirmed", "cancelled", "completed"
    @ServerTimestamp var createdAt: Timestamp? = null // Timestamp of when the request was created
) {
    // No-argument constructor for Firestore deserialization
    constructor() : this(
        id = null,
        patientId = null,
        patientName = null,
        professionalId = null,
        professionalName = null,
        appointmentTimestamp = null,
        reasonForVisit = null,
        status = null,
        createdAt = null
    )
}
