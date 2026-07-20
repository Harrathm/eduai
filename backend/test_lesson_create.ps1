$r = Invoke-RestMethod -Uri "http://localhost:8001/auth/login" -Method POST -Body "username=admin@eduai.platform&password=admin123"
$token = $r.access_token

$body = @"
{
    "title": "Test Lesson API",
    "lesson_type": "text",
    "order": 10
}
"@

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8001/api/admin/lessons?module_id=4" -Method POST -Headers @{ Authorization = "Bearer $token" } -ContentType "application/json" -Body $body
    $response | ConvertTo-Json
} catch {
    Write-Host "Error: $_"
}