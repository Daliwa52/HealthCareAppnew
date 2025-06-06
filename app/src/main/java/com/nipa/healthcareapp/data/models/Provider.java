package com.nipa.healthcareapp.data.models;

import java.util.ArrayList;
import java.util.List;

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
        this.rating = 0f;
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
        this.availability = availability;
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
}
