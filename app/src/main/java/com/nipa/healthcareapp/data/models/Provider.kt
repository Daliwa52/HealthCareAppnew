package com.nipa.healthcareapp.data.models

public data class Provider(
    val id: String = "",
    val name: String = "",
    val email: String = "",
    val specialty: String = "",
    val rating: Float = 0f,
    val profilePicture: String = "",
    val availability: List<String> = emptyList()
)
