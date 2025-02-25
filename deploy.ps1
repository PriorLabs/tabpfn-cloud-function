# Deployment script for Cloud Function

# Set error action preference
$ErrorActionPreference = "Stop"

Write-Host "Starting deployment process..."

try {
    # Verify gcloud is installed and authenticated
    Write-Host "Verifying gcloud installation..."
    $gcloud = Get-Command gcloud -ErrorAction SilentlyContinue
    if (-not $gcloud) {
        throw "gcloud is not installed. Please install Google Cloud SDK first."
    }

    # Get current project
    $project = gcloud config get-value project
    Write-Host "Deploying to project: $project"

    # Build and deploy
    Write-Host "Starting cloud build..."
    gcloud builds submit --config=cloudbuild.yaml

    # Get the function URL
    Write-Host "Getting function URL..."
    # Replace 'your-region' with your actual GCP region (e.g., 'us-central1', 'europe-west1')
    $url = gcloud functions describe infer-category --region=your-region --format="value(serviceConfig.uri)"
    
    Write-Host "Deployment completed successfully!"
    Write-Host "Function URL: $url"
    
    # Create a test payload
    $testPayload = @{
        transactions = @(
            @{
                id = "test1"
                dateOp = "01/03/2024"
                amount = -50.0
                transaction_description = "SNCF PARIS"
            }
        )
    } | ConvertTo-Json

    # Save test payload
    $testPayload | Out-File -FilePath "test_payload.json" -Encoding UTF8
    Write-Host "Test payload saved to test_payload.json"
    Write-Host "You can test the function using:"
    Write-Host "curl -X POST $url -H 'Content-Type: application/json' -d @test_payload.json"

} catch {
    Write-Host "Error during deployment: $_" -ForegroundColor Red
    exit 1
} 