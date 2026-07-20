$body = @{
    title = "Test Lesson"
    lesson_type = "text"
    content_text = "Test content"
} | ConvertTo-Json

$token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwic2Nob29sX2lkIjoxLCJleHAiOjE3NzgxMzY5MDF9.ssNJSSHBj4wVjUcOULtagvWKsyNKlRlU9pZ2KwlhYC0"

Invoke-WebRequest -Uri "http://localhost:8000/api/admin/modules/12/lessons" -Method POST -Headers @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
} -Body $body