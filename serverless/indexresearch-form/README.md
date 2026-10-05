# IndexResearch lead form backend

Production handler for the public contact/research-request form on indexresearch.ru.

## Yandex Cloud Function

- Runtime: Python 3.14
- Entrypoint: `index.handler`
- Memory: 128 MB
- Timeout: 10 seconds
- Service account: attach a service account with the `postbox.sender` role
- Public function: enabled, because browsers call the HTTPS endpoint directly
- Static keys: not required; the handler uses the service-account IAM token available in the function context

## Environment variables

```text
POSTBOX_FROM=form@indexresearch.ru
POSTBOX_TO=research@indexresearch.ru
ALLOWED_ORIGINS=https://indexresearch.ru,https://www.indexresearch.ru
MAX_BODY_BYTES=32768
MIN_FILL_SECONDS=1.5
```

These values contain no credentials. Do not add API keys, SMTP passwords or IAM tokens to this repository.

## Postbox

Create and verify the `indexresearch.ru` domain in Yandex Cloud Postbox in the same cloud folder as the service account used by the function. Easy DKIM is the preferred setup.

The function sends a raw MIME message through the Postbox HTTP API so a validated visitor email can be used as `Reply-To`.

## Frontend endpoint

After the function is deployed, put its public invocation URL into:

```text
/assets/form-config.js
```

Example:

```js
window.INDEXRESEARCH_FORM_ENDPOINT = 'https://functions.yandexcloud.net/<function-id>';
```

No secret is exposed by publishing this URL.
