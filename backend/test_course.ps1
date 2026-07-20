$token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwic2Nob29sX2lkIjoxLCJleHAiOjE3NzgxMzY5MDF9.ssNJSSHBj4wVjUcOULtagvWKsyNKlRlU9pZ2KwlhYC0"

Invoke-WebRequest -Uri "http://localhost:8000/api/admin/courses/36" -Method GET -Headers @{
    "Authorization" = "Bearer $token"
}