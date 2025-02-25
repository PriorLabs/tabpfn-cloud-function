# Get the function URL
$functionUrl = gcloud functions describe infer_category --format='value(url)'
Write-Host "Function URL: $functionUrl"

# Read the test payload
$payload = Get-Content -Path "test_payload.json" -Raw

# Send the request
Write-Host "`nSending test request..."
$response = Invoke-RestMethod -Uri $functionUrl -Method Post -Body $payload -ContentType "application/json"

# Pretty print the response
Write-Host "`nResponse:"
$response | ConvertTo-Json -Depth 10 