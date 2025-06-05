$oldBase = "c:\Users\hp amd\AndroidStudioProjects\HealthCareApp\app\src\main\java\com\example\healthcareapp"
$newBase = "c:\Users\hp amd\AndroidStudioProjects\HealthCareApp\app\src\main\java\com\nipa\healthcareapp"

# Get all Kotlin files
$files = Get-ChildItem -Path $oldBase -Recurse -File -Filter *.kt

# Create a mapping of old to new paths
$fileMap = @{ }
foreach ($file in $files) {
    $relativePath = $file.FullName.Substring($oldBase.Length + 1)
    $newPath = Join-Path $newBase $relativePath
    $fileMap[$file.FullName] = $newPath
}

# Process each file
foreach ($oldPath in $fileMap.Keys) {
    $newPath = $fileMap[$oldPath]
    
    # Create directories if they don't exist
    $newDir = [System.IO.Path]::GetDirectoryName($newPath)
    if (-not (Test-Path $newDir)) {
        New-Item -ItemType Directory -Path $newDir -Force
    }
    
    # Read and update content
    $content = Get-Content $oldPath
    $newContent = $content -replace 'package com.example.healthcareapp', 'package com.nipa.healthcareapp'
    
    # Write to new location
    Set-Content -Path $newPath -Value $newContent
    
    # Remove old file
    Remove-Item $oldPath
}
