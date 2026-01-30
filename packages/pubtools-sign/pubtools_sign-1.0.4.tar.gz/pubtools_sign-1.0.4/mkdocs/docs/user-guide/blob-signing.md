# Blob signing

## Messaging signer

Messaging signer works as client which communicates with the server via messaging bus. User data
to be signed are wrapped into signing requests and sent to the server. The server replies with 
signed requests which are composed from the original signing request and the JSON signature encrypted by
gpg and base64 encoded.

## Example

```bash
pubtools-sign-msg-blob-sign \
    --signing-key testing \
    --config-file ~/.config/pubtools-sign/conf-hacbs.yaml \
    --task-id 32e729ee-62ae-4d17-b067-d86f6d89939f \
    --blob-file <path-to-a-file>
```


