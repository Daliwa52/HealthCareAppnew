package com.nipa.healthcareapp.viewmodel;

import android.util.Log;

import androidx.annotation.NonNull;
import androidx.lifecycle.LiveData;
import androidx.lifecycle.MutableLiveData;
import androidx.lifecycle.ViewModel;

import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.auth.FirebaseUser;
import com.google.firebase.firestore.DocumentSnapshot;
import com.google.firebase.firestore.FirebaseFirestore;

import java.util.Map;
import java.util.Objects;

public class HomeViewModel extends ViewModel {

    private static final String TAG = "HomeViewModel";

    // Inner User class (POJO)
    public static class User {
        private String id;
        private String name;
        private String email; // Example field
        private String profilePictureUrl; // Example field

        // Default constructor for Firestore deserialization
        public User() {}

        public User(String id, String name, String email, String profilePictureUrl) {
            this.id = id;
            this.name = name;
            this.email = email;
            this.profilePictureUrl = profilePictureUrl;
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
        public String getProfilePictureUrl() {
            return profilePictureUrl;
        }

        // Setters (optional, but good for mutable POJOs if needed)
        public void setId(String id) {
            this.id = id;
        }
        public void setName(String name) {
            this.name = name;
        }
        public void setEmail(String email) {
            this.email = email;
        }
        public void setProfilePictureUrl(String profilePictureUrl) {
            this.profilePictureUrl = profilePictureUrl;
        }

        @Override
        public boolean equals(Object o) {
            if (this == o) return true;
            if (o == null || getClass() != o.getClass()) return false;
            User user = (User) o;
            return Objects.equals(id, user.id) &&
                   Objects.equals(name, user.name) &&
                   Objects.equals(email, user.email) &&
                   Objects.equals(profilePictureUrl, user.profilePictureUrl);
        }

        @Override
        public int hashCode() {
            return Objects.hash(id, name, email, profilePictureUrl);
        }

        @NonNull
        @Override
        public String toString() {
            return "User{" +
                   "id='" + id + '\'' +
                   ", name='" + name + '\'' +
                   ", email='" + email + '\'' +
                   ", profilePictureUrl='" + profilePictureUrl + '\'' +
                   '}';
        }
    }

    private final MutableLiveData<User> _user = new MutableLiveData<>();
    public final LiveData<User> user = _user; // Made final as it's not reassigned

    private final FirebaseAuth auth;
    private final FirebaseFirestore db;

    public HomeViewModel() {
        auth = FirebaseAuth.getInstance();
        db = FirebaseFirestore.getInstance();
        loadUserData();
    }

    private void loadUserData() {
        FirebaseUser currentUser = auth.getCurrentUser();
        if (currentUser != null) {
            String userId = currentUser.getUid();
            db.collection("users")
                .document(userId)
                .get()
                .addOnSuccessListener(documentSnapshot -> {
                    if (documentSnapshot.exists()) {
                        Map<String, Object> data = documentSnapshot.getData();
                        if (data != null) {
                            String name = data.get("name") instanceof String ? (String) data.get("name") : "";
                            String email = data.get("email") instanceof String ? (String) data.get("email") : ""; // Example
                            String profilePic = data.get("profilePictureUrl") instanceof String ? (String) data.get("profilePictureUrl") : ""; // Example

                            User loadedUser = new User(documentSnapshot.getId(), name, email, profilePic);
                            _user.postValue(loadedUser); // Use postValue for safety from listeners
                            Log.d(TAG, "User data loaded: " + loadedUser);
                        } else {
                            Log.w(TAG, "User document data is null for user: " + userId);
                             _user.postValue(null); // Or a default/empty user object
                        }
                    } else {
                        Log.w(TAG, "User document does not exist for user: " + userId);
                        _user.postValue(null); // Or a default/empty user object
                    }
                })
                .addOnFailureListener(e -> {
                    Log.e(TAG, "Error loading user data", e);
                    _user.postValue(null); // Or handle error state appropriately
                });
        } else {
            Log.w(TAG, "No current user to load data for.");
            _user.postValue(null); // No user logged in
        }
    }
}
