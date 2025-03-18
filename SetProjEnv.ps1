[CmdletBinding()]
param (
    [Parameter(Mandatory=$true)]
    [ValidateSet("Claude", "Cursor")]
    [string]$proj
)

# Display which project environment is being set
Write-Host "Setting environment variables for $proj project..."

# Set environment variables based on project type
if ($proj -eq "Claude") {
    # Claude project environment variables
    $env:LLM_PROJ = "$env:KAGGLE_EXPTS\LLM-projects"
    $env:SAP_HARNESS_HOME = "$env:LLM_PROJ\code\supply_chain\mini_meta_harness" 
    $env:SAP_HARNESS_CONFIG = "$env:SAP_HARNESS_HOME\test_structure.json"
    $env:MINI_META = "$env:LLM_PROJ\code\supply_chain\mini_meta_harness"
    
    # Display the configured variables
    Write-Host "LLM_PROJ: $env:LLM_PROJ"
    Write-Host "SAP_HARNESS_HOME: $env:SAP_HARNESS_HOME"
    Write-Host "SAP_HARNESS_CONFIG: $env:SAP_HARNESS_CONFIG"
    Write-Host "MINI_META: $env:MINI_META"
}
elseif ($proj -eq "Cursor") {
    # Cursor project environment variables
    $env:CURSOR_PROJ = "$env:KAGGLE_EXPTS\cursor_projects"
    $env:SAP_HARNESS_HOME = "$env:CURSOR_PROJ\mini_meta_harness" 
    $env:SAP_HARNESS_CONFIG = "$env:SAP_HARNESS_HOME\test_structure.json"
    $env:MINI_META = "$env:CURSOR_PROJ\mini_meta_harness"
    
    # Display the configured variables
    Write-Host "CURSOR_PROJ: $env:CURSOR_PROJ"
    Write-Host "SAP_HARNESS_HOME: $env:SAP_HARNESS_HOME"
    Write-Host "SAP_HARNESS_CONFIG: $env:SAP_HARNESS_CONFIG"
    Write-Host "MINI_META: $env:MINI_META"
}

Write-Host "Environment variables set successfully for $proj project." 