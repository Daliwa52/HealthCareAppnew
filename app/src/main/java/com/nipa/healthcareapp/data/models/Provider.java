package com.nipa.healthcareapp.data.models;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

public class Provider {
    private String id;
    private String name;
    private String email;
    private String specialty;
    private float rating;
    private String profilePicture;
    private List<String> availability;

    // Default constructor
    public Provider() {
        this.id = "";
        this.name = "";
        this.email = "";
        this.specialty = "";
        this.rating = 0.0f;
        this.profilePicture = "";
        this.availability = new ArrayList<>();
    }

    // Constructor with all fields
    public Provider(String id, String name, String email, String specialty, float rating, String profilePicture, List<String> availability) {
        this.id = id;
        this.name = name;
        this.email = email;
        this.specialty = specialty;
        this.rating = rating;
        this.profilePicture = profilePicture;
        this.availability = availability != null ? availability : new ArrayList<>();
    }

    // Getters
    public String getId() {
        return id;
    }

    public String getName() {
        return name;
    }

    public String getEmail() {
        return email;
    }

    public String getSpecialty() {
        return specialty;
    }

    public float getRating() {
        return rating;
    }

    public String getProfilePicture() {
        return profilePicture;
    }

    public List<String> getAvailability() {
        return availability;
    }

    // Setters
    public void setId(String id) {
        this.id = id;
    }

    public void setName(String name) {
        this.name = name;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public void setSpecialty(String specialty) {
        this.specialty = specialty;
    }

    public void setRating(float rating) {
        this.rating = rating;
    }

    public void setProfilePicture(String profilePicture) {
        this.profilePicture = profilePicture;
    }

    public void setAvailability(List<String> availability) {
        this.availability = availability;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Provider provider = (Provider) o;
        return Float.compare(provider.rating, rating) == 0 &&
               Objects.equals(id, provider.id) &&
               Objects.equals(name, provider.name) &&
               Objects.equals(email, provider.email) &&
               Objects.equals(specialty, provider.specialty) &&
               Objects.equals(profilePicture, provider.profilePicture) &&
               Objects.equals(availability, provider.availability);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id, name, email, specialty, rating, profilePicture, availability);
    }

    @Override
    public String toString() {
        return "Provider{" +
               "id='" + id + '\'' +
               ", name='" + name + '\'' +
               ", email='" + email + '\'' +
               ", specialty='" + specialty + '\'' +
               ", rating=" + rating +
               ", profilePicture='" + profilePicture + '\'' +
               ", availability=" + availability +
               '}';
    }
}
