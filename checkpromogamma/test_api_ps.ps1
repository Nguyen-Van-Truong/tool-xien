# Test Gamma/Stripe API using PowerShell
Write-Host "Testing Gamma Promo Code API..." -ForegroundColor Green

$code = "RZZKK46F"
$url = "https://api.stripe.com/v1/promotion_codes/$code"

Write-Host "Testing code: $code" -ForegroundColor Yellow
Write-Host "URL: $url" -ForegroundColor Yellow

$headers = @{
    "Authorization" = "Bearer pk_live_51MS6sAE3HBB5yrHt6gBd276SL4CGS2kGGPA4gkYgfOdKB3g9E1HMaUyoEi0Z47s0h1FVD1MuYaZ3Ay32U13xqeH400NPSkhlYc"
    "Accept" = "application/json"
    "User-Agent" = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
    "Origin" = "https://billing.gamma.app"
    "Referer" = "https://billing.gamma.app/c/pay/cs_live_b1rSDhKOm0RPZNr16MgX3aidRbrwjHhfaCDYWHZPTJyC6KJdRMsxwqGj0i"
}

try {
    Write-Host "Making request..." -ForegroundColor Cyan
    $response = Invoke-WebRequest -Uri $url -Headers $headers -Method GET -TimeoutSec 10

    Write-Host "Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "Response:" -ForegroundColor Green
    Write-Host $response.Content -ForegroundColor White

} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        Write-Host "Status Code: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
        $stream = $_.Exception.Response.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($stream)
        $responseBody = $reader.ReadToEnd()
        Write-Host "Error Response: $responseBody" -ForegroundColor Red
    }
}

Write-Host "`nTest completed!" -ForegroundColor Green



