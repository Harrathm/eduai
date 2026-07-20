$token = (Invoke-RestMethod -Uri "http://localhost:8000/auth/login" -Method POST -ContentType "application/x-www-form-urlencoded" -Body "username=admin@eduai.platform&password=admin123").access_token

# Test directly via curl to see error
$ErrorActionPreference = "Continue"
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/learner/courses/1/preview" -Method GET -Headers @{Authorization="Bearer $token"} -TimeoutSec 30
    $response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 3
} catch {
    $_.Exception.Response.StatusCode
    $_.Exception.Message
}