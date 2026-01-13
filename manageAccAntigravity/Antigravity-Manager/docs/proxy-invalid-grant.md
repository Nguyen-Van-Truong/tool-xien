# Proxy: handling `invalid_grant` refresh failures

## Problem
When an OAuth `refresh_token` is revoked/expired, Google token refresh returns `invalid_grant`.
Previously the proxy could repeatedly pick the same broken account, repeatedly fail refresh, and eventually return a `503` error due to an effectively unusable token pool.

## Behavior after this change
### 1) Persistently disable the account on `invalid_grant`
- When token refresh fails with `invalid_grant`, the proxy marks that account as disabled on disk:
  - `disabled: true`
  - `disabled_at: <unix timestamp>`
  - `disabled_reason: "invalid_grant: …"` (truncated)
- The account is also removed from the in-memory token pool, preventing retry storms.

### 2) Skip disabled accounts when building the token pool
- During `TokenManager::load_accounts`, account JSON files with `disabled: true` are skipped.
- Reload clears the in-memory pool and re-reads the on-disk state so disables/enables take effect immediately.

### 3) Immediate reload when accounts change (if proxy is running)
Account mutations that affect proxy availability trigger a best-effort token pool reload when the proxy is running:
- Adding an account
- Completing OAuth login
- Updating tokens via the UI (account upsert)

## Re-enabling an account
If a user updates credentials in the UI (token upsert) and changes either `refresh_token` or `access_token`, the account is automatically re-enabled by clearing:
- `disabled`
- `disabled_reason`
- `disabled_at`

This supports the workflow where a revoked token is replaced manually without requiring a proxy restart.

## Data model / compatibility
Accounts gain three new fields:
- `disabled` (`bool`, default `false`)
- `disabled_reason` (`string | null`)
- `disabled_at` (`number | null`)

These fields are optional and use defaults, so existing account files continue to load.

## Operational notes
- The `disabled_reason` is truncated to avoid bloating the account JSON.
- No secrets are intentionally written into `disabled_reason`; it is derived from the refresh error string.
- If desired, the UI can surface these fields to explain why an account is no longer used by the proxy.

## Testing (suggested)
- Reproduce: force an account to have a revoked/invalid `refresh_token` and trigger a proxy request that requires refresh.
- Expected:
  - Proxy logs show the `invalid_grant` failure and account disable.
  - The account is removed from the token pool and will not be selected again.
  - After updating the token via UI, the account is re-enabled and becomes eligible without restarting the proxy.
