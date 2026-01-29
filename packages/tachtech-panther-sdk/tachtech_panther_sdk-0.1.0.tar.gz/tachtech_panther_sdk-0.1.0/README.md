# TachTech Panther SDK

A comprehensive Python SDK for [Panther Security](https://panther.com) that provides:

1. **API Client** - Clean wrapper for REST and GraphQL APIs
2. **Detection Framework** - Tools for writing and testing detection rules
3. **SPL Converter** - Convert Splunk SPL detection rules to Panther Python rules

## Installation

```bash
pip install tachtech-panther-sdk
```

Or install from source:

```bash
git clone https://github.com/TachTech-Engineering/panther_sdk
cd panther_sdk
pip install -e .
```

## Quick Start

### API Client

```python
from panther_sdk import PantherClient

# Initialize with environment variables
# Set PANTHER_API_HOST and PANTHER_API_TOKEN
client = PantherClient()

# Or with explicit credentials
client = PantherClient(
    api_host="your-instance.runpanther.net",
    api_token="your-api-token"
)

# List open critical alerts
for alert in client.alerts.list(status="OPEN", severity="CRITICAL"):
    print(f"{alert.severity}: {alert.title}")

# Get a specific alert
alert = client.alerts.get("alert-id")

# Update alert status
client.alerts.update("alert-id", status="TRIAGED")

# Close the client when done
client.close()
```

### Using Context Manager

```python
with PantherClient() as client:
    alerts = list(client.alerts.list(severity="HIGH"))
```

### Async Support

```python
import asyncio
from panther_sdk import PantherClient

async def main():
    async with PantherClient() as client:
        async for alert in client.alerts.alist(status="OPEN"):
            print(alert.title)

asyncio.run(main())
```

## API Resources

### Alerts

```python
# List alerts with filters
alerts = client.alerts.list(
    status="OPEN",
    severity="CRITICAL",
    detection_id="AWS.CloudTrail.RootActivity",
    max_items=100,
)

# Get alert details
alert = client.alerts.get("alert-id")

# Update an alert
client.alerts.update("alert-id", status="RESOLVED", assignee_id="user-id")

# Batch update alerts
client.alerts.batch_update(
    alert_ids=["alert-1", "alert-2"],
    status="CLOSED"
)

# Get events for an alert
for event in client.alerts.get_events("alert-id"):
    print(event.data)

# Add a comment
client.alerts.add_comment("alert-id", "Investigation notes...")
```

### Rules

```python
# List rules
for rule in client.rules.list(enabled=True, severity="HIGH"):
    print(rule.id)

# Get a rule
rule = client.rules.get("AWS.CloudTrail.RootActivity")

# Create a rule
rule = client.rules.create(
    id="Custom.MyRule",
    body="def rule(event): return event.get('eventName') == 'DeleteBucket'",
    severity="HIGH",
    log_types=["AWS.CloudTrail"],
    display_name="S3 Bucket Deletion",
)

# Update a rule
client.rules.update("Custom.MyRule", enabled=False)

# Delete a rule
client.rules.delete("Custom.MyRule")
```

### Policies

```python
# List policies
for policy in client.policies.list(enabled=True):
    print(policy.id)

# Create a policy
policy = client.policies.create(
    id="Custom.S3.Encryption",
    body="def policy(resource): return resource.get('Encryption') is not None",
    severity="HIGH",
    resource_types=["AWS.S3.Bucket"],
)
```

### Queries (Data Lake)

```python
# Execute a query and wait for results
result = client.queries.execute(
    sql="SELECT * FROM panther_logs.public.aws_cloudtrail LIMIT 100",
    timeout=60.0,
)

print(f"Rows: {len(result.results)}")
for row in result.results:
    print(row)

# Or manage query lifecycle manually
query = client.queries.create("SELECT COUNT(*) FROM panther_logs.public.aws_cloudtrail")
while query.status == "RUNNING":
    query = client.queries.get_results(query.query_id)
print(query.results)
```

### Users & Roles

```python
# List users
for user in client.users.list():
    print(f"{user.email} - {user.role_name}")

# Invite a user
user = client.users.invite(
    email="new.user@example.com",
    role_id="analyst-role-id",
)

# List roles
for role in client.roles.list():
    print(f"{role.name}: {role.permissions}")
```

### GraphQL API

```python
# Execute custom GraphQL queries
result = client.graphql.execute("""
    query {
        alerts(input: {first: 10, status: [OPEN]}) {
            edges {
                node {
                    id
                    title
                    severity
                }
            }
        }
    }
""")

# Use convenience methods
stats = client.graphql.get_organization_stats()
print(f"Total alerts: {stats['organizationStats']['alertStats']['total']}")
```

## Detection Framework

Write detection rules as Python classes:

```python
from panther_sdk.detections import Rule, Severity, LogType

class BruteForceLogin(Rule):
    id = "Custom.BruteForce.Login"
    log_types = [LogType.OKTA_SYSTEM_LOG]
    severity = Severity.HIGH
    threshold = 5
    dedup_period_minutes = 10

    tags = ["Authentication", "Brute Force"]

    def rule(self, event):
        return (
            event.get("eventType") == "user.session.start"
            and event.get("outcome", {}).get("result") == "FAILURE"
        )

    def title(self, event):
        actor = event.get("actor", {}).get("alternateId", "Unknown")
        return f"Brute force attempt detected for {actor}"

    def dedup(self, event):
        return event.get("actor", {}).get("alternateId", self.id)

    def alert_context(self, event):
        return {
            "actor": event.get("actor"),
            "client": event.get("client"),
            "outcome": event.get("outcome"),
        }
```

### Testing Detections

```python
from panther_sdk.detections import Rule, Severity, LogType
from panther_sdk.detections.testing import DetectionTester, TestCase

class MyRule(Rule):
    id = "Custom.MyRule"
    log_types = [LogType.AWS_CLOUDTRAIL]
    severity = Severity.MEDIUM

    def rule(self, event):
        return event.get("eventName") == "DeleteBucket"

    def title(self, event):
        bucket = event.get("requestParameters", {}).get("bucketName", "unknown")
        return f"S3 Bucket Deleted: {bucket}"

# Create test cases
tests = [
    TestCase(
        name="Should alert on DeleteBucket",
        data={
            "eventName": "DeleteBucket",
            "requestParameters": {"bucketName": "my-bucket"}
        },
        expected_result=True,
        expected_title="S3 Bucket Deleted: my-bucket",
    ),
    TestCase(
        name="Should not alert on CreateBucket",
        data={"eventName": "CreateBucket"},
        expected_result=False,
    ),
]

# Run tests
tester = DetectionTester(MyRule())
results = tester.run_tests(tests)

for result in results:
    status = "PASS" if result.passed else "FAIL"
    print(f"{status}: {result.name}")
```

### Helper Functions

```python
from panther_sdk.detections import (
    deep_get,
    is_ip_in_network,
    is_private_ip,
    pattern_match,
    aws_cloudtrail_success,
)

# Safe nested dictionary access
email = deep_get(event, "user.profile.email", "unknown")

# IP address helpers
if is_ip_in_network(ip, "10.0.0.0/8"):
    print("Internal IP")

if is_private_ip(ip):
    print("Private IP")

# Pattern matching with wildcards
if pattern_match(email, "*@suspicious-domain.com"):
    print("Suspicious email domain")

# CloudTrail helpers
if aws_cloudtrail_success(event):
    print("API call succeeded")
```

## SPL to Panther Converter

Convert Splunk SPL detection rules to Panther Python rules automatically.

### Basic Usage

```python
from panther_sdk.converters.splunk import SPLToPantherConverter

converter = SPLToPantherConverter()

# Convert a simple SPL query
result = converter.convert(
    spl='eventName=DeleteBucket',
    rule_id='Custom.AWS.DeleteBucket'
)

print(result.source_code)
```

### Converting Threshold Rules

The converter automatically detects threshold patterns like `stats count by X | where count > N`:

```python
spl = '''
index=okta sourcetype=okta:im:log eventType="user.session.start" outcome.result=FAILURE
| stats count by actor.alternateId
| where count > 5
'''

result = converter.convert(spl, rule_id='Custom.Okta.BruteForceLogin')
print(result.source_code)
```

**Output:**
```python
from panther_sdk.detections import Rule, Severity, LogType
from panther_sdk.detections import deep_get

class OktaBruteForceLogin(Rule):
    id = "Custom.Okta.BruteForceLogin"
    log_types = ["Okta.SystemLog"]
    severity = Severity.MEDIUM
    threshold = 5
    dedup_period_minutes = 60

    def rule(self, event: dict) -> bool:
        return (
            event.get("eventType") == "user.session.start"
            and deep_get(event, "outcome.result") == "FAILURE"
        )

    def title(self, event: dict) -> str:
        identifier = deep_get(event, "actor.alternateId", "Unknown")
        return f"Detection triggered for {identifier}"

    def dedup(self, event: dict) -> str:
        result = deep_get(event, "actor.alternateId")
        return str(result) if result else self.id
```

### Converter Options

```python
# Set custom severity
result = converter.convert(
    spl='eventName=DeleteTrail',
    rule_id='Custom.AWS.DeleteTrail',
    severity='CRITICAL'  # or use Splunk scale 1-6
)

# Custom class name
result = converter.convert(
    spl='action=login status=failed',
    rule_id='Custom.FailedLogin',
    class_name='MyCustomRuleName'
)
```

### Batch Conversion

Convert multiple SPL rules at once and get recommendations for which rules should be scheduled queries:

```python
rules = [
    {'spl': 'eventName=DeleteBucket', 'rule_id': 'Custom.AWS.DeleteBucket'},
    {'spl': 'eventName=DeleteTrail', 'rule_id': 'Custom.AWS.DeleteTrail', 'severity': 'CRITICAL'},
    {'spl': 'index=main | join user [search index=users]', 'rule_id': 'Custom.UserCorrelation'},
]

result = converter.convert_batch(rules)

# All rules are converted to streaming Python rules
for rule in result.rules:
    print(f"Generated {rule.class_name}")

# Get summary of recommendations
print(result.get_summary())
```

**Output:**
```
Converted 3 rules:
  - Streaming (real-time): 2
  - Recommended for scheduled queries: 1

Rules recommended for SCHEDULED QUERIES:
--------------------------------------------------
  Custom.UserCorrelation (UserCorrelation)
    - Contains JOIN - correlates multiple data sources
```

### Scheduled Query Recommendations

The converter analyzes each SPL query and recommends whether it should be a:
- **Streaming Rule** (real-time Python) - Simple field comparisons, threshold rules
- **Scheduled Query** (SQL) - Complex aggregations, joins, lookups

Patterns that trigger scheduled query recommendations:
- `join` commands (cross-source correlation)
- `lookup` commands (reference table enrichment)
- Subsearches (nested queries)
- `transaction` commands (session analysis)
- Statistical aggregations (`avg`, `stdev`, `percentile`, `median`)
- Large time windows (`earliest=-7d` or more)

```python
# Check individual rule recommendation
result = converter.convert('index=main | join user [search index=users]', 'Custom.Test')
print(result.recommended_type)  # RecommendedDetectionType.SCHEDULED
print(result.recommendation_reasons)  # ['Contains JOIN - correlates multiple data sources']
```

### Convenience Function

For quick one-off conversions:

```python
from panther_sdk.converters.splunk import convert_spl

result = convert_spl(
    spl='user=admin* AND action=delete',
    rule_id='Custom.AdminDelete'
)
```

### Supported SPL Features

| Feature | Support | Notes |
|---------|---------|-------|
| `field=value` | Full | Direct comparison |
| `field=val*` | Full | Uses `pattern_match()` |
| `AND/OR/NOT` | Full | Boolean logic |
| `stats count` | Full | Threshold rule detection |
| `stats by X` | Full | Generates `dedup()` method |
| `eval` | Full | Common functions (if, case, string ops) |
| `where` | Full | Filter conditions |
| `rex` | Full | Generates `re.search()` |
| `table/fields` | Info | Generates `alert_context()` |
| `join` | TODO | Comment with suggestion |
| `lookup` | TODO | Comment with suggestion |
| `subsearch [...]` | TODO | Comment with suggestion |
| `` `macro` `` | TODO | Needs expansion |

### Handling Unsupported Features

Unsupported SPL features are captured and embedded as TODO comments:

```python
spl = 'index=main | join user [search index=users]'
result = converter.convert(spl, 'Custom.JoinExample')

# result.todos contains: ['command: Unsupported command: join']
# Generated code includes:
#   # TODO: Manual conversion required
#   # COMMAND: Unsupported command: join
#   #   Suggestion: Consider using scheduled queries with correlation
```

### Log Type Inference

The converter automatically infers Panther log types from SPL sourcetypes:

| Splunk Sourcetype | Panther Log Type |
|-------------------|------------------|
| `aws:cloudtrail` | `AWS.CloudTrail` |
| `okta:im:log` | `Okta.SystemLog` |
| `crowdstrike:events` | `CrowdStrike.FDREvent` |
| `github:audit` | `GitHub.Audit` |
| `ms:o365:management:activity` | `Microsoft365.Audit` |

### Generated Test Code

Each conversion also generates unit test scaffolding:

```python
result = converter.convert(spl, rule_id='Custom.Test')
print(result.test_code)  # pytest-compatible test template
```

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `PANTHER_API_HOST` | Panther instance hostname |
| `PANTHER_API_TOKEN` | API token for authentication |
| `PANTHER_API_VERSION` | API version (default: "v1") |
| `PANTHER_TIMEOUT` | Request timeout in seconds (default: 30) |
| `PANTHER_VERIFY_SSL` | Verify SSL certificates (default: true) |
| `PANTHER_DEBUG` | Enable debug logging (default: false) |

### Configuration File

Create a `.env` file in your project root:

```env
PANTHER_API_HOST=your-instance.runpanther.net
PANTHER_API_TOKEN=your-api-token
PANTHER_DEBUG=false
```

## Error Handling

```python
from panther_sdk import PantherClient
from panther_sdk.exceptions import (
    NotFoundError,
    AuthenticationError,
    RateLimitError,
)

client = PantherClient()

try:
    alert = client.alerts.get("nonexistent-id")
except NotFoundError as e:
    print(f"Alert not found: {e.resource_id}")
except AuthenticationError:
    print("Invalid API token")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
```

## Development

### Setup

```bash
git clone https://github.com/TachTech-Engineering/panther_sdk
cd panther_sdk
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Type Checking

```bash
mypy panther_sdk
```

### Linting

```bash
ruff check panther_sdk
```

### Publishing to PyPI

1. Install build tools:
```bash
pip install build twine
```

2. Build the package:
```bash
python -m build
```

3. Upload to PyPI:
```bash
twine upload dist/*
```

Use `__token__` as username and your [PyPI API token](https://pypi.org/manage/account/token/) as password.

## License

MIT License - see [LICENSE](LICENSE) for details.
