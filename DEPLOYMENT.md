# Flex Nickname API — patched deployment notes

## Confirmed findings

The deployed `/test` endpoint is online. The supplied UID/password pair was rejected by the upstream guest-login service with `auth_error`, so nickname change cannot start until a valid, matching guest credential is supplied.

The project also had a deployment compatibility problem: the generated protobuf files require protobuf runtime 6.30.0, while `requirements.txt` pinned protobuf 4.25.1. The previous `app.py` silently replaced the real protobuf classes with dummy classes when imports failed; that made MajorLogin and nickname-change requests invalid. The patch pins protobuf 6.30.0, explicitly includes Flask, and removes the silent dummy fallback.

## Deploy

From the project root, deploy the patched files to the same Vercel project:

```bash
vercel --prod
```

After deployment, verify:

```text
https://YOUR-DOMAIN/test
https://YOUR-DOMAIN/login?uid=UID&password=PASSWORD
```

Use a newly generated guest password that belongs to the same UID. Do not place credentials in public URLs, logs, screenshots, or frontend code in production; prefer a POST endpoint with a JSON body and server-side secrets for a production-grade API.

## Files changed

- `requirements.txt`: Flask 3.1.0 and protobuf 6.30.0 are now pinned.
- `app.py`: real protobuf imports are required, credential fragments are no longer logged, and upstream authentication failures are reported clearly.

## Important limitation

No code change can make an invalid, expired, revoked, or mismatched UID/password pair authenticate. The upstream service must accept the credential first. The patched API is ready to proceed once `/login` returns an access token; the complete nickname-change flow should then be tested on a test account before production use.
