# Frontend Clerk API Integration

The backend API is protected by an AWS API Gateway JWT authorizer. The frontend
must call protected endpoints with a Clerk JWT bearer token.

## Protected endpoints

- `POST /api/v1/readings`
- `GET /api/v1/readings`
- `GET /api/v1/readings/{reading_id}`
- `DELETE /api/v1/readings/{reading_id}`
- `GET /api/v1/readings/{reading_id}/recording`
- `GET /api/v1/readings/{reading_id}/corrected-text.md`
- `GET /api/v1/readings/{reading_id}/original-text`
- `GET /api/v1/readings/{reading_id}/timing-map`
- `POST /api/v1/readings/{reading_id}/retry`
- `GET /api/v1/jobs`
- `GET /api/v1/settings`
- `PUT /api/v1/settings`
- `GET /api/v1/tts-options`

Public endpoints:

- `GET /api/v1/health`
- `GET /docs`
- `GET /redoc`
- `GET /openapi.json`

## Clerk setup

Create a Clerk JWT template for backend API calls, for example:

```txt
Template name: przeczytai-api
```

The token must include an audience claim that matches Terraform:

```json
{
  "aud": "przeczytai-api-dev"
}
```

The configured `clerk_jwt_audience` must match this `aud`. Set the backend
Terraform values (`clerk_jwt_issuer`, `clerk_jwt_audience`) as described in
[`infrastructure/README.md`](../infrastructure/README.md). To confirm the
issuer, generate one token from the template, decode it, and copy the `iss`
claim.

## Frontend request

For protected API calls, get a Clerk token from the template and send it as a
bearer token:

```ts
const token = await getToken({ template: "przeczytai-api" });

await fetch(`${apiBaseUrl}/api/v1/readings`, {
  method: "GET",
  headers: {
    Authorization: `Bearer ${token}`,
  },
});
```

For requests with JSON bodies:

```ts
await fetch(`${apiBaseUrl}/api/v1/readings`, {
  method: "POST",
  headers: {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({ original_text: "Ala ma kota." }),
});
```

Do not send `userId`. Do not send `x-api-key`. The backend uses the verified
JWT `sub` claim as the reading owner.
