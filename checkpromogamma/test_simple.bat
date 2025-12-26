@echo off
echo Testing Gamma Promo Code API...
echo.

echo Testing code: RZZKK46F
curl -s -H "Authorization: Bearer pk_live_51MS6sAE3HBB5yrHt6gBd276SL4CGS2kGGPA4gkYgfOdKB3g9E1HMaUyoEi0Z47s0h1FVD1MuYaZ3Ay32U13xqeH400NPSkhlYc" ^
     -H "Accept: application/json" ^
     -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0" ^
     -H "Origin: https://billing.gamma.app" ^
     -H "Referer: https://billing.gamma.app/c/pay/cs_live_b1rSDhKOm0RPZNr16MgX3aidRbrwjHhfaCDYWHZPTJyC6KJdRMsxwqGj0i" ^
     "https://api.stripe.com/v1/promotion_codes/RZZKK46F"

echo.
echo.
echo Testing code: TEST123
curl -s -H "Authorization: Bearer pk_live_51MS6sAE3HBB5yrHt6gBd276SL4CGS2kGGPA4gkYgfOdKB3g9E1HMaUyoEi0Z47s0h1FVD1MuYaZ3Ay32U13xqeH400NPSkhlYc" ^
     -H "Accept: application/json" ^
     -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0" ^
     -H "Origin: https://billing.gamma.app" ^
     -H "Referer: https://billing.gamma.app/c/pay/cs_live_b1rSDhKOm0RPZNr16MgX3aidRbrwjHhfaCDYWHZPTJyC6KJdRMsxwqGj0i" ^
     "https://api.stripe.com/v1/promotion_codes/TEST123"

echo.
echo.
echo Test completed!
pause

