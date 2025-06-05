$files = Get-ChildItem -Path "c:\Users\hp amd\AndroidStudioProjects\HealthCareApp\app\src\main\java\com\example\healthcareapp" -Recurse -File -Filter *.kt

foreach ($file in $files) {
    # Read the file content
    $content = Get-Content $file.FullName
    
    # Update package declaration
    $newContent = $content -replace 'package com.example.healthcareapp', 'package com.nipa.healthcareapp'
    
    # Create new path in the new package structure
    $relativePath = $file.FullName.Substring("c:\Users\hp amd\AndroidStudioProjects\HealthCareApp\app\src\main\java\com\example\healthcareapp".Length + 1)
    $newPath = "c:\Users\hp amd\AndroidStudioProjects\HealthCareApp\app\src\main\java\com\nipa\healthcareapp" + $relativePath
    
    # Create directories if they don't exist
    $newDir = [System.IO.Path]::GetDirectoryName($newPath)
    if (-not (Test-Path $newDir)) {
        New-Item -ItemType Directory -Path $newDir -Force
    }
    
    # Write the updated content to the new location
    Set-Content -Path $newPath -Value $newContent
    
    # Remove the old file
    Remove-Item $file.FullName
}
