# Release 10.1.1 - 2026-03-31

## Summary

Bug fix release focusing on RGV587 risk control handling and BitBrowser API resilience.

## Fixed

### WebSocket Transport (ws_live)

- **RGV587 server overload handling**: When the token API returns `RGV587_ERROR::SM::哎哟喂,被挤爆啦` (server-side rate limiting), the system now uses a 600-second backoff instead of repeatedly refreshing cookies. This prevents aggravating the server-side rate limit with unnecessary requests.
- **MTOP risk control marking**: Added explicit `risk_control` marker in mtop responses to avoid false success states when risk control blocks requests.
- **MTOP secret env aliases**: Added compatibility for both `MTOP_APP_SECRET` and `XIANYU_MTOP_APP_SECRET` environment variables.
- **MTOP secret warning**: Added startup warning when MTOP secret is not configured.
- **Token pair consistency**: Added `_m_h5_tk` / `_m_h5_tk_enc` pair consistency correction during cookie merge to prevent `FAIL_BIZ_PARAM_INVALID` from mismatched token pairs.
- **Payload appKey fallback**: When `MTOP_APP_SECRET` is missing, the payload appKey now falls back to `XIANYU_MTOP_APP_KEY` instead of sending empty value.
- **not support appkey handling**: Token API payload appKey now has fallback to `XIANYU_MTOP_PAYLOAD_APP_KEY` to avoid `FAIL_BIZ_400100001::not support appkey` errors.
- **Auto-retry on not support appkey**: When token API returns "not support appkey", automatically retry with fallback payload appKey.

### Slider Solver

- **BitBrowser API retry**: Increased BitBrowser API call robustness by adding 3 retries with 2-second delays before falling back to local Chrome (previously failed immediately on first error).
- **JSON parse error handling**: Fixed issue where empty API responses were incorrectly treated as successful.

### Other Modules

- `modules/quote/engine`: Enhanced fallback reason tracking and network error classification.
- `modules/followup/service`: Improved config loading to only degrade on missing config, not other errors.
- `modules/messages/reply_engine`: Added missing error logging for config reading and compliance checks.
- `client/api/dashboard`: `getUnmatchedStats` now properly rejects on network failures instead of false success.
- `tests/conftest`: Improved mock strictness with `spec_set` to reduce false positives.

## Upgrade Notes

No breaking changes. Upgrade from 10.1.0 directly.

## Downloads

- Source code: https://github.com/G3niusYukki/realxianyu/archive/refs/tags/v10.1.1.tar.gz
- Wheel: Available via PyPI after release
