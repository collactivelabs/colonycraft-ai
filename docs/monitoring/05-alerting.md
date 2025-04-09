# Alerting

## Alert Rules

| Category | Alert | Condition | Severity | Response |
|----------|-------|-----------|----------|----------|
| **System** | High CPU Usage | CPU > 80% for 5 minutes | Warning | Scale resources |
| **System** | Critical CPU Usage | CPU > 95% for 2 minutes | Critical | Auto-scale, notify team |
| **System** | Memory Usage | Memory > 85% for 5 minutes | Warning | Investigate memory leak |
| **System** | Disk Space | Disk space < 10% | Warning | Add storage, clean logs |
| **Application** | High Error Rate | Error rate > 5% for 5 minutes | Critical | Alert on-call, roll back |
| **Application** | API Latency | P95 latency > 500ms for 5 minutes | Warning | Investigate performance |
| **Application** | Endpoint Down | Health check fails for 2 minutes | Critical | Alert on-call, failover |
| **LLM** | Provider Error | Error rate for provider > 10% | Warning | Switch to alternate provider |
| **Database** | Connection Exhaustion | Pool usage > 80% for 5 minutes | Warning | Increase pool size |
| **Database** | Query Performance | Slow query detected | Info | Review query patterns |
| **Security** | Authentication Spike | Auth failures > 20 in 1 minute | Warning | Review for brute force |
| **Security** | API Key Misuse | Unusual API key usage pattern | Warning | Review for key compromise |

## Alert Channels

Alerts are dispatched through multiple channels based on severity and type:

1. **PagerDuty**: Critical alerts requiring immediate response
2. **Slack**: Warnings and informational alerts
3. **Email**: Daily and weekly summaries
4. **SMS**: Critical alerts as backup to PagerDuty

## Alert Integration

Alerting is configured in Prometheus Alertmanager:

```yaml
# alertmanager.yml
global:
  resolve_timeout: 5m
  slack_api_url: 'https://hooks.slack.com/services/TXXXXXXXX/BXXXXXXXX/XXXXXXXXXXXXXXX'
  pagerduty_url: 'https://events.pagerduty.com/v2/enqueue'

route:
  group_by: ['alertname', 'job', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: 'slack-notifications'
  routes:
  - match:
      severity: critical
    receiver: 'pagerduty-critical'
    continue: true
  - match:
      severity: warning
    receiver: 'slack-notifications'

receivers:
- name: 'pagerduty-critical'
  pagerduty_configs:
  - service_key: 'your_pagerduty_service_key'
    send_resolved: true
- name: 'slack-notifications'
  slack_configs:
  - channel: '#monitoring'
    send_resolved: true
    title: "{{ .GroupLabels.alertname }}"
    text: "{{ range .Alerts }}{{ .Annotations.description }}\n{{ end }}"
```

## Alert Severity Levels

The alert system uses the following severity levels:

1. **Critical**: System is down or severely impacted, requires immediate attention
2. **Warning**: Potential issue that could escalate, requires prompt investigation
3. **Info**: Notable event that does not require immediate action

## Alert Fatigue Prevention

To prevent alert fatigue, the following measures are implemented:

1. **Grouping**: Related alerts are grouped to reduce noise
2. **Rate Limiting**: Limits on the frequency of similar alerts
3. **Deduplication**: Identical alerts are combined
4. **Auto-resolution**: Alerts are automatically resolved when conditions return to normal
5. **Smart Routing**: Alerts are routed to the most appropriate team members

## On-Call Rotation

On-call responsibilities are managed through PagerDuty:

1. **Primary On-Call**: First responder for all critical alerts
2. **Secondary On-Call**: Backup for the primary responder
3. **Escalation Path**: Defined process for escalating unresolved issues
4. **Rotation Schedule**: Weekly rotation with handoff procedures

## Runbooks

Each alert is linked to a detailed runbook containing:

1. **Alert Description**: Explanation of what triggered the alert
2. **Impact Assessment**: Potential user impact
3. **Diagnosis Steps**: How to investigate the issue
4. **Resolution Actions**: Steps to resolve the issue
5. **Escalation Path**: When and how to escalate the issue

Example runbook template:

```markdown
# High Error Rate Alert Runbook

## Alert Description
This alert is triggered when the error rate exceeds 5% for 5 minutes.

## Impact Assessment
- Users may experience failed requests
- API dependents may see increased error responses
- Data processing may be incomplete

## Diagnosis Steps
1. Check recent deployments in [Deployment Dashboard](https://deploy.colonycraft.ai)
2. Examine error logs in Kibana using the query: `level:ERROR AND timestamp:[now-15m TO now]`
3. Check service health metrics in [Service Dashboard](https://grafana.colonycraft.ai/d/service-health)
4. Verify LLM provider status at provider status pages

## Resolution Actions
1. If recent deployment, consider rolling back with `kubectl rollout undo deployment/api-service`
2. If LLM provider issue, switch to backup provider in config
3. If resource constraint, scale the affected service: `kubectl scale deployment/api-service --replicas=5`
4. If database issues, check DB performance dashboard and optimize queries

## Escalation Path
1. If unable to resolve in 15 minutes, escalate to backend team lead
2. If business impact is severe, notify VP of Engineering
```
