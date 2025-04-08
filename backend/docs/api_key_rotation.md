# API Key Rotation

API key rotation is a security best practice that involves periodically replacing existing API keys with new ones. This helps limit the damage that could occur if a key is compromised and reduces the risk of unauthorized access to your API resources.

## Key Features

1. **Generate New API Keys**: Create new API keys to replace existing ones
2. **Grace Period**: Keep old keys working for a configurable period to ensure a smooth transition
3. **Automatic Expiration**: Old keys are automatically expired after the grace period
4. **Notifications**: Warning headers in API responses when using soon-to-expire keys
5. **Compromise Recovery**: Option to immediately invalidate a key if it's been compromised
6. **Audit Trail**: Full history of key rotations for security auditing

## How API Key Rotation Works

### Standard Rotation Flow

1. **Initiate Rotation**: Call the `/api/v1/api-keys/{key_id}/rotate` endpoint with the ID of the key you want to rotate
2. **Generate New Key**: The system creates a new API key with the same or modified permissions
3. **Grace Period**: The old key continues to work for a configurable period (default: 7 days)
4. **Warning Headers**: When using the old key during the grace period, warning headers are included in API responses
5. **Automatic Expiration**: After the grace period, the old key stops working

### Compromised Key Flow

If a key has been compromised:

1. **Immediate Invalidation**: Set `was_compromised=true` when rotating to immediately invalidate the old key
2. **No Grace Period**: The old key is immediately revoked with no grace period
3. **Security Headers**: Special security headers are included in the rotation response
4. **Audit Record**: A record is created in the rotation history marking the key as compromised

## API Endpoints

### Create a New API Key

```http
POST /api/v1/api-keys
```

Request body:
```json
{
  "name": "My API Key",
  "scopes": ["read", "write"],
  "expires_in_days": 90
}
```

### Rotate an API Key

```http
POST /api/v1/api-keys/{key_id}/rotate
```

Request body:
```json
{
  "name": "New Production Key",
  "scopes": ["read", "write"],
  "expires_in_days": 90,
  "grace_period_days": 7,
  "was_compromised": false
}
```

### List API Keys

```http
GET /api/v1/api-keys?include_rotated=true
```

The `include_rotated` parameter controls whether to include keys that are in the grace period after rotation.

### Get API Key Rotation History

```http
GET /api/v1/api-keys/{key_id}/rotation-history
```

### Get Soon-to-Expire API Keys

```http
GET /api/v1/api-keys/expiring/soon?days=7
```

## Warning Headers

When using a key that is in its grace period after rotation, the following headers will be included in API responses:

```
Warning: 299 saas-api "API key is deprecated and will expire on 2023-01-08T00:00:00Z"
X-API-Key-Expiry: 2023-01-08T00:00:00Z
X-API-Key-Replacement-Prefix: newprefix
Link: </docs#section/Authentication/API-Key-Rotation>; rel="help"; title="API Key Rotation Guide"
```

## Best Practices

1. **Regular Rotation**: Rotate API keys regularly as part of your security procedures
2. **Monitoring**: Monitor the usage of keys in their grace period to ensure clients are updated
3. **Automation**: Implement client-side automation to detect warning headers and update keys
4. **Credentials Management**: Store API keys securely and follow the principle of least privilege
5. **Response to Compromise**: Have a clear process for handling compromised keys
6. **Audit**: Regularly review the API key rotation history for security auditing
