try {
    $token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwic2Nob29sX2lkIjoxLCJleHAiOjE3NzgxMzczNzZ9.ZVwWnLZMhvE_o9LJbue07G6EMPbmm_H32Fb3JRLjVFM"
    
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/admin/courses/36" -Method GET -Headers @{ Authorization = "Bearer $token" }
    $response | ConvertTo-Json -Depth 10
} catch {
    Write-Host "Error: $_"
    $_.Exception.Response.StatusCode
}