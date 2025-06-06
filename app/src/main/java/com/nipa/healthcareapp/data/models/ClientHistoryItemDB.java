package com.nipa.healthcareapp.data.models;

import androidx.room.Entity;
import androidx.room.PrimaryKey;
// import androidx.room.TypeConverters; // Assuming TypeConverters might be needed for LocalDate or List<String>
import androidx.annotation.NonNull;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
// Additional imports for validation if specific checks are done e.g. TextUtils
import android.text.TextUtils;


// Renamed Enum as per instruction
enum ConsultationTypeDB {
    IN_PERSON,
    ONLINE,
    PHONE_CALL,
    OTHER
}

@Entity(tableName = "client_history_item")
// Converters would be needed for Room to handle LocalDate and List<String>
// e.g. @TypeConverters({DateConverter.class, StringListConverter.class, ConsultationTypeConverter.class})
public class ClientHistoryItemDB {

    @PrimaryKey
    @NonNull
    private String id;

    @NonNull
    private String providerId;

    @NonNull
    private String patientId;

    @NonNull
    private String patientName;

    @NonNull
    // Room needs a TypeConverter for custom objects like LocalDate
    private LocalDate consultationDate;

    @NonNull
    // Room needs a TypeConverter for enums, or store as String/Int
    private ConsultationTypeDB consultationType;

    private String notes;

    // Room needs a TypeConverter for List<String>
    private List<String> attachments;

    private boolean synced;

    // Default constructor
    public ClientHistoryItemDB() {
        this.id = UUID.randomUUID().toString();
        this.attachments = new ArrayList<>();
        this.notes = "";
        this.synced = true;
        // NonNull fields like providerId, patientId, etc., must be set via setters or parameterized constructor
        // For Room, a no-arg constructor is often required. Fields will be set by Room using setters or reflection.
    }

    // Parameterized constructor - useful for object creation before inserting into DB
    // Room primarily uses the default constructor and setters.
    public ClientHistoryItemDB(@NonNull String providerId, @NonNull String patientId, @NonNull String patientName,
                               @NonNull LocalDate consultationDate, @NonNull ConsultationTypeDB consultationType,
                               String notes, List<String> attachments, boolean synced) {
        this.id = UUID.randomUUID().toString();
        this.providerId = providerId;
        this.patientId = patientId;
        this.patientName = patientName;
        this.consultationDate = consultationDate;
        this.consultationType = consultationType;
        this.notes = (notes != null) ? notes : "";
        this.attachments = (attachments != null) ? attachments : new ArrayList<>();
        this.synced = synced;
    }

    // Constructor that includes ID - useful if ID is known (e.g. when fetching from a source)
    public ClientHistoryItemDB(@NonNull String id, @NonNull String providerId, @NonNull String patientId, @NonNull String patientName,
                               @NonNull LocalDate consultationDate, @NonNull ConsultationTypeDB consultationType,
                               String notes, List<String> attachments, boolean synced) {
        this.id = id;
        this.providerId = providerId;
        this.patientId = patientId;
        this.patientName = patientName;
        this.consultationDate = consultationDate;
        this.consultationType = consultationType;
        this.notes = (notes != null) ? notes : "";
        this.attachments = (attachments != null) ? attachments : new ArrayList<>();
        this.synced = synced;
    }


    // Getters
    @NonNull
    public String getId() { return id; }
    @NonNull
    public String getProviderId() { return providerId; }
    @NonNull
    public String getPatientId() { return patientId; }
    @NonNull
    public String getPatientName() { return patientName; }
    @NonNull
    public LocalDate getConsultationDate() { return consultationDate; }
    @NonNull
    public ConsultationTypeDB getConsultationType() { return consultationType; }
    public String getNotes() { return notes; }
    public List<String> getAttachments() { return attachments; }
    public boolean isSynced() { return synced; }

    // Setters
    public void setId(@NonNull String id) { this.id = id; }
    public void setProviderId(@NonNull String providerId) { this.providerId = providerId; }
    public void setPatientId(@NonNull String patientId) { this.patientId = patientId; }
    public void setPatientName(@NonNull String patientName) { this.patientName = patientName; }
    public void setConsultationDate(@NonNull LocalDate consultationDate) { this.consultationDate = consultationDate; }
    public void setConsultationType(@NonNull ConsultationTypeDB consultationType) { this.consultationType = consultationType; }
    public void setNotes(String notes) { this.notes = notes; }
    public void setAttachments(List<String> attachments) { this.attachments = attachments; }
    public void setSynced(boolean synced) { this.synced = synced; }

    // Static validation method (placeholder for actual logic)
    public static List<String> validate(ClientHistoryItemDB item) {
        List<String> errors = new ArrayList<>();
        if (item == null) {
            errors.add("ClientHistoryItemDB cannot be null.");
            return errors;
        }
        if (TextUtils.isEmpty(item.getProviderId())) {
            errors.add("Provider ID cannot be empty.");
        }
        if (TextUtils.isEmpty(item.getPatientId())) {
            errors.add("Patient ID cannot be empty.");
        }
        if (TextUtils.isEmpty(item.getPatientName())) {
            errors.add("Patient name cannot be empty.");
        }
        if (item.getConsultationDate() == null) {
            errors.add("Consultation date cannot be null.");
        }
        // Example: Check if consultationDate is in the future (if that's a rule)
        // if (item.getConsultationDate() != null && item.getConsultationDate().isAfter(LocalDate.now())) {
        //     errors.add("Consultation date cannot be in the future.");
        // }
        if (item.getConsultationType() == null) {
            errors.add("Consultation type cannot be null.");
        }
        // Add more validation logic as per the original Kotlin file's validate method
        // e.g., for notes length, attachment format, etc.
        // This is a placeholder as the original Kotlin validation logic was not provided.
        if (item.getNotes() == null) { // notes = "" by default, but could be set to null
             errors.add("Notes should not be null, use empty string instead.");
        }
        if (item.getAttachments() == null) { // attachments = new ArrayList<>() by default
            errors.add("Attachments list should not be null, use empty list instead.");
        }
        return errors;
    }
}
