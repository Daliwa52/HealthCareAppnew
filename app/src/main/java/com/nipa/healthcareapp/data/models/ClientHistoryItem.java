package com.nipa.healthcareapp.data.models;

import androidx.annotation.NonNull; // Added for PrimaryKey
import androidx.room.Entity;
import androidx.room.PrimaryKey;
// import androidx.room.TypeConverters; // Not used in the provided snippet, but kept for reference

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.UUID;

@Entity(tableName = "client_history_item")
public class ClientHistoryItem {

    @PrimaryKey
    @NonNull
    private String id;

    private String providerId;
    private String patientId;
    private String patientName;
    private LocalDate consultationDate; // Ensure TypeConverter for LocalDate is set up for Room
    private ConsultationType consultationType; // Ensure TypeConverter for ConsultationType is set up for Room (or it's stored as String)
    private String notes;
    private List<String> attachments; // Ensure TypeConverter for List<String> is set up for Room
    private boolean synced;

    // Default constructor
    public ClientHistoryItem() {
        this.id = UUID.randomUUID().toString();
        this.notes = "";
        this.attachments = new ArrayList<>();
        this.synced = true;
        // providerId, patientId, patientName, consultationDate, consultationType will be null/default
        // This might be an issue if they are expected to be non-null.
        // The all-args constructor should be the primary way to create valid instances.
    }

    // Constructor with all fields
    public ClientHistoryItem(@NonNull String id, String providerId, String patientId, String patientName,
                             LocalDate consultationDate, ConsultationType consultationType,
                             String notes, List<String> attachments, boolean synced) {
        this.id = id;
        this.providerId = providerId;
        this.patientId = patientId;
        this.patientName = patientName;
        this.consultationDate = consultationDate;
        this.consultationType = consultationType;
        this.notes = notes;
        this.attachments = attachments != null ? attachments : new ArrayList<>();
        this.synced = synced;
    }

    // Getters
    @NonNull
    public String getId() {
        return id;
    }

    public String getProviderId() {
        return providerId;
    }

    public String getPatientId() {
        return patientId;
    }

    public String getPatientName() {
        return patientName;
    }

    public LocalDate getConsultationDate() {
        return consultationDate;
    }

    public ConsultationType getConsultationType() {
        return consultationType;
    }

    public String getNotes() {
        return notes;
    }

    public List<String> getAttachments() {
        return attachments;
    }

    public boolean isSynced() { // Standard getter for boolean
        return synced;
    }

    // Setters
    public void setId(@NonNull String id) {
        this.id = id;
    }

    public void setProviderId(String providerId) {
        this.providerId = providerId;
    }

    public void setPatientId(String patientId) {
        this.patientId = patientId;
    }

    public void setPatientName(String patientName) {
        this.patientName = patientName;
    }

    public void setConsultationDate(LocalDate consultationDate) {
        this.consultationDate = consultationDate;
    }

    public void setConsultationType(ConsultationType consultationType) {
        this.consultationType = consultationType;
    }

    public void setNotes(String notes) {
        this.notes = notes;
    }

    public void setAttachments(List<String> attachments) {
        this.attachments = attachments;
    }

    public void setSynced(boolean synced) {
        this.synced = synced;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        ClientHistoryItem that = (ClientHistoryItem) o;
        return synced == that.synced &&
               id.equals(that.id) && // @NonNull, so no Objects.equals needed
               Objects.equals(providerId, that.providerId) &&
               Objects.equals(patientId, that.patientId) &&
               Objects.equals(patientName, that.patientName) &&
               Objects.equals(consultationDate, that.consultationDate) &&
               consultationType == that.consultationType &&
               Objects.equals(notes, that.notes) &&
               Objects.equals(attachments, that.attachments);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id, providerId, patientId, patientName, consultationDate, consultationType, notes, attachments, synced);
    }

    @Override
    public String toString() {
        return "ClientHistoryItem{" +
               "id='" + id + '\'' +
               ", providerId='" + providerId + '\'' +
               ", patientId='" + patientId + '\'' +
               ", patientName='" + patientName + '\'' +
               ", consultationDate=" + consultationDate +
               ", consultationType=" + consultationType +
               ", notes='" + notes + '\'' +
               ", attachments=" + attachments +
               ", synced=" + synced +
               '}';
    }

    public static List<String> validate(ClientHistoryItem item) {
        List<String> errors = new ArrayList<>();
        // ... validation logic ...
        // Example:
        // if (item.getProviderId() == null || item.getProviderId().trim().isEmpty()) {
        //     errors.add("Provider ID cannot be empty.");
        // }
        // if (item.getPatientId() == null || item.getPatientId().trim().isEmpty()) {
        //     errors.add("Patient ID cannot be empty.");
        // }
        // if (item.getPatientName() == null || item.getPatientName().trim().isEmpty()) {
        //     errors.add("Patient name cannot be empty.");
        // }
        // if (item.getConsultationDate() == null) {
        //    errors.add("Consultation date cannot be empty.");
        // }
        // if (item.getConsultationType() == null) {
        //    errors.add("Consultation type cannot be empty.");
        // }
        return errors;
    }
}
