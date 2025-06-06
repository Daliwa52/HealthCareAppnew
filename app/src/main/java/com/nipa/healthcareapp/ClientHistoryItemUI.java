package com.nipa.healthcareapp;

import java.time.LocalDate;

// Enum for UI-specific consultation types
enum ConsultationTypeUI {
    GENERAL_CHECKUP,
    SPECIALIST,
    EMERGENCY,
    FOLLOW_UP
}

public class ClientHistoryItemUI {
    private String patientName;
    private ConsultationTypeUI consultationType;
    private LocalDate consultationDate;
    private String notes;

    // Constructor with all fields
    public ClientHistoryItemUI(String patientName, ConsultationTypeUI consultationType, LocalDate consultationDate, String notes) {
        this.patientName = patientName;
        this.consultationType = consultationType;
        this.consultationDate = consultationDate;
        this.notes = notes;
    }

    // Getters
    public String getPatientName() {
        return patientName;
    }

    public ConsultationTypeUI getConsultationType() {
        return consultationType;
    }

    public LocalDate getConsultationDate() {
        return consultationDate;
    }

    public String getNotes() {
        return notes;
    }

    // Setters
    public void setPatientName(String patientName) {
        this.patientName = patientName;
    }

    public void setConsultationType(ConsultationTypeUI consultationType) {
        this.consultationType = consultationType;
    }

    public void setConsultationDate(LocalDate consultationDate) {
        this.consultationDate = consultationDate;
    }

    public void setNotes(String notes) {
        this.notes = notes;
    }
}
