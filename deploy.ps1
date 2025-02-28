# Deployment script for TabPFN Cloud Function

# Set error action preference
$ErrorActionPreference = "Stop"

# Configuration - Edit these values
$region = "us-central1"  # Change to your preferred region
$useServiceAccount = $false  # Set to $true if using a service account
$serviceAccount = "your-service-account@your-project-id.iam.gserviceaccount.com"

Write-Host "Starting deployment process..." -ForegroundColor Cyan

try {
    # Verify gcloud is installed and authenticated
    Write-Host "Verifying gcloud installation..."
    $gcloud = Get-Command gcloud -ErrorAction SilentlyContinue
    if (-not $gcloud) {
        throw "gcloud is not installed. Please install Google Cloud SDK first."
    }

    # Get current project
    $project = gcloud config get-value project
    Write-Host "Deploying to project: $project" -ForegroundColor Green
    
    # Verify .env.yaml exists
    if (-not (Test-Path .env.yaml)) {
        Write-Host "Warning: .env.yaml not found, creating template file..." -ForegroundColor Yellow
        "GCS_BUCKET: `"your-bucket-name`"
USE_GCS: `"true`"
USE_MOCK: `"false`"
TABPFN_API_TOKEN: `"your-api-token-here`"" | Out-File -FilePath ".env.yaml" -Encoding UTF8
        Write-Host "Please edit .env.yaml with your actual values before continuing." -ForegroundColor Yellow
        $continue = Read-Host "Continue with deployment? (y/n)"
        if ($continue -ne "y") {
            throw "Deployment cancelled by user."
        }
    }
    
    # Check if cloudbuild.yaml exists
    if (-not (Test-Path cloudbuild.yaml)) {
        Write-Host "Warning: cloudbuild.yaml not found, using direct deployment." -ForegroundColor Yellow
        
        # Deploy using gcloud functions deploy command
        Write-Host "Deploying function using gcloud..." -ForegroundColor Cyan
        
        $deployCommand = "gcloud functions deploy infer-category --gen2 --region=$region --runtime=python310 --source=. --entry-point=infer_category --trigger-http --memory=2048MB --timeout=540s --env-vars-file=.env.yaml"
        
        if ($useServiceAccount) {
            $deployCommand += " --service-account=$serviceAccount"
        }
        
        Write-Host "Executing: $deployCommand" -ForegroundColor Gray
        Invoke-Expression $deployCommand
    }
    else {
        # Build and deploy using Cloud Build
        Write-Host "Starting cloud build..." -ForegroundColor Cyan
        gcloud builds submit --config=cloudbuild.yaml
    }

    # Get the function URL
    Write-Host "Getting function URL..." -ForegroundColor Cyan
    $url = gcloud functions describe infer-category --region=$region --format="value(serviceConfig.uri)"
    
    Write-Host "Deployment completed successfully!" -ForegroundColor Green
    Write-Host "Function URL: $url" -ForegroundColor Green
    
    # Update the Google Apps Script Code.gs file with new URL
    Write-Host "Would you like to update Code.gs with the new function URL? (y/n)"
    $updateCode = Read-Host
    if ($updateCode -eq "y") {
        $codeGsContent = Get-Content -Path "Code.gs" -Raw
        $updatedContent = $codeGsContent -replace "const CLOUD_FUNCTION_URL = '.*?';", "const CLOUD_FUNCTION_URL = '$url';"
        Set-Content -Path "Code.gs" -Value $updatedContent
        Write-Host "Code.gs updated with new function URL." -ForegroundColor Green
    }
    
    # Create a test payload
    $testPayload = @{
        transactions = @(
            @{
                id = "test1"
                dateOp = "01/03/2024"
                amount = -50.0
                transaction_description = "SNCF PARIS"
            },
            @{
                id = "test2"
                dateOp = "01/03/2024"
                amount = 2000.0
                transaction_description = "SALARY DEPOSIT"
            }
        )
    } | ConvertTo-Json

    # Save test payload
    $testPayload | Out-File -FilePath "test_payload.json" -Encoding UTF8
    Write-Host "Test payload saved to test_payload.json" -ForegroundColor Cyan
    Write-Host "You can test the function using:"
    Write-Host "curl -X POST $url -H 'Content-Type: application/json' -d @test_payload.json" -ForegroundColor Yellow

} catch {
    Write-Host "Error during deployment: $_" -ForegroundColor Red
    exit 1
} 