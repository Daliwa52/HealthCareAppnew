# Define paths
$oldBase = "c:\Users\hp amd\AndroidStudioProjects\HealthCareApp\app\src\main\java\com\example\healthcareapp"
$newBase = "c:\Users\hp amd\AndroidStudioProjects\HealthCareApp\app\src\main\java\com\nipa\healthcareapp"
$layoutDir = "c:\Users\hp amd\AndroidStudioProjects\HealthCareApp\app\src\main\res\layout"

# Function to update package declarations
function Update-PackageDeclaration {
    param([string]$content)
    return $content -replace 'package com\.example\.healthcareapp', 'package com\.nipa\.healthcareapp'
}

# Function to update imports
function Update-Imports {
    param([string]$content)
    return $content -replace 'import com\.example\.healthcareapp', 'import com\.nipa\.healthcareapp'
}

# Function to update layout references
function Update-LayoutReferences {
    param([string]$content)
    return $content -replace 'android:name="com\.example\.healthcareapp', 'android:name="com\.nipa\.healthcareapp'
}

# Process Kotlin files
Write-Host "Processing Kotlin files..."
$files = Get-ChildItem -Path $oldBase -Recurse -File -Filter *.kt
foreach ($file in $files) {
    $relativePath = $file.FullName.Substring($oldBase.Length + 1)
    $newPath = Join-Path $newBase $relativePath
    
    # Create directories if they don't exist
    $newDir = [System.IO.Path]::GetDirectoryName($newPath)
    if (-not (Test-Path $newDir)) {
        New-Item -ItemType Directory -Path $newDir -Force
    }
    
    # Read and update content
    $content = Get-Content $file.FullName -Raw
    $newContent = $content | Update-PackageDeclaration | Update-Imports
    
    # Write to new location
    Set-Content -Path $newPath -Value $newContent
    
    # Remove old file
    Remove-Item $file.FullName
}

# Process layout files
Write-Host "Processing layout files..."
$layoutFiles = Get-ChildItem -Path $layoutDir -Recurse -File -Filter *.xml
foreach ($file in $layoutFiles) {
    $content = Get-Content $file.FullName -Raw
    $newContent = $content | Update-LayoutReferences
    Set-Content -Path $file.FullName -Value $newContent
}

# Update AndroidManifest.xml
Write-Host "Updating AndroidManifest.xml..."
$manifestPath = "c:\Users\hp amd\AndroidStudioProjects\HealthCareApp\app\src\main\AndroidManifest.xml"
$manifestContent = Get-Content $manifestPath -Raw
$newManifestContent = $manifestContent | Update-LayoutReferences
Set-Content -Path $manifestPath -Value $newManifestContent

Write-Host "Package name update complete!"
