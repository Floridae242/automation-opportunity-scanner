# OpenID Connect SSO setup

The application keeps local sign-in available until an OpenID Connect provider is configured and verified. Do not direct users to an SSO button before all values below are supplied through the deployment secret store.

Set these environment variables:

- `SSO_ISSUER`: the HTTPS issuer URL published by the identity provider.
- `SSO_CLIENT_ID`: the registered application client ID.
- `SSO_CLIENT_SECRET`: the client secret, stored only in the deployment secret store.
- `SSO_REDIRECT_URI`: the exact HTTPS callback URL registered at the provider.

Owners can inspect the configuration state from Organization access. The status endpoint deliberately returns only variable names that are missing; it never returns credentials.

Before enabling an SSO login flow, verify issuer discovery, authorization-code callback, signed ID-token validation, email verification policy, tenant/domain restrictions, and logout behavior against the selected provider.
