# Avro Integration

Tessera supports [Apache Avro](https://avro.apache.org/) schemas for Kafka topics, event streams, and other data assets that use Avro serialization.

## Installation

Avro support requires the optional `fastavro` dependency:

```bash
pip install tessera-contracts[avro]
```

Or with uv:

```bash
uv add tessera-contracts[avro]
```

Without `fastavro`, Tessera falls back to basic structural validation.

## Publishing Avro Contracts

### Via API

```bash
curl -X POST "$TESSERA_URL/api/v1/assets/{asset_id}/contracts" \
  -H "Authorization: Bearer $TESSERA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "schema": {
      "type": "record",
      "name": "UserEvent",
      "namespace": "com.example.events",
      "fields": [
        {"name": "id", "type": "string"},
        {"name": "email", "type": "string"},
        {"name": "created_at", "type": "long", "logicalType": "timestamp-millis"}
      ]
    },
    "schema_format": "avro",
    "compatibility_mode": "backward"
  }'
```

### Via Python SDK

```python
from tessera_sdk import TesseraClient

client = TesseraClient()

# Create asset for Kafka topic
asset = client.assets.create(
    fqn="kafka.events.user_created",
    owner_team_id=team.id,
    resource_type="kafka_topic"
)

# Publish Avro contract
result = client.assets.publish_contract(
    asset_id=asset.id,
    schema={
        "type": "record",
        "name": "UserCreatedEvent",
        "namespace": "com.example.events",
        "fields": [
            {"name": "id", "type": "string"},
            {"name": "email", "type": "string"},
            {"name": "name", "type": ["null", "string"], "default": None}
        ]
    },
    schema_format="avro",
    version="1.0.0"
)
```

## Avro Schema Requirements

Tessera validates that Avro schemas conform to the [Avro specification](https://avro.apache.org/docs/current/specification/):

### Record Types

Records must have:
- `type`: Must be `"record"`
- `name`: Schema name (required)
- `fields`: Array of field definitions (required)

```json
{
  "type": "record",
  "name": "User",
  "fields": [
    {"name": "id", "type": "string"},
    {"name": "email", "type": "string"}
  ]
}
```

### Enum Types

```json
{
  "type": "enum",
  "name": "Status",
  "symbols": ["PENDING", "ACTIVE", "DELETED"]
}
```

### Array Types

```json
{
  "type": "array",
  "items": "string"
}
```

### Map Types

```json
{
  "type": "map",
  "values": "long"
}
```

### Union Types (Optional Fields)

```json
{
  "name": "middle_name",
  "type": ["null", "string"],
  "default": null
}
```

## Breaking Change Detection

Tessera detects breaking changes in Avro schemas based on the compatibility mode:

### Backward Compatibility (Default)

Breaking changes:
- Removing a field without a default value
- Adding a required field without a default
- Changing field type to incompatible type
- Removing enum symbols

Compatible changes:
- Adding optional fields (with defaults)
- Adding new enum symbols
- Widening numeric types (int -> long)

### Forward Compatibility

Breaking changes:
- Adding fields (consumers don't know about them)
- Adding enum symbols
- Widening types

Compatible changes:
- Removing optional fields
- Removing enum symbols

### Full Compatibility

Breaking if any change affects either readers or writers.

## Impact Analysis

Check the impact of schema changes before publishing:

```python
impact = client.assets.check_impact(
    asset_id=asset.id,
    proposed_schema={
        "type": "record",
        "name": "UserCreatedEvent",
        "fields": [
            {"name": "id", "type": "string"},
            # Removed 'email' field - breaking change!
            {"name": "name", "type": ["null", "string"], "default": None}
        ]
    },
    schema_format="avro"
)

if not impact.safe_to_publish:
    print(f"Breaking changes: {impact.breaking_changes}")
    print(f"Affected consumers: {impact.affected_consumers}")
```

## Schema Registry Integration

Tessera can work alongside Confluent Schema Registry or other Avro registries:

```python
import requests

# Fetch schema from registry
response = requests.get(
    f"{SCHEMA_REGISTRY_URL}/subjects/user-events-value/versions/latest"
)
avro_schema = response.json()["schema"]

# Publish to Tessera
client.assets.publish_contract(
    asset_id=asset.id,
    schema=json.loads(avro_schema),
    schema_format="avro",
    version="1.0.0"
)
```

## CI/CD Integration

Validate Avro schemas in your CI pipeline:

```yaml
# GitHub Actions
- name: Validate Avro Schema
  run: |
    RESPONSE=$(curl -s -X POST "$TESSERA_URL/api/v1/assets/$ASSET_ID/impact" \
      -H "Authorization: Bearer $TESSERA_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "proposed_schema": '"$(cat schema.avsc)"',
        "schema_format": "avro"
      }')

    SAFE=$(echo "$RESPONSE" | jq -r '.safe_to_publish')
    if [ "$SAFE" != "true" ]; then
      echo "Breaking changes detected!"
      echo "$RESPONSE" | jq '.breaking_changes'
      exit 1
    fi
```

## Related

- [Assets & Contracts](../concepts/assets-contracts.md) - Schema format details
- [Breaking Changes](../concepts/breaking-changes.md) - Compatibility modes
- [Python SDK](./python-sdk.md) - Client library
