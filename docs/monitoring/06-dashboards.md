# Dashboards

The ColonyCraft AI platform utilizes a comprehensive set of dashboards to provide visibility into system health and performance. All dashboards are implemented in Grafana with Prometheus as the primary data source.

## Dashboard Organization

Dashboards are organized in a hierarchical structure:

1. **Overview**: High-level system health
2. **System**: Infrastructure and platform components
3. **Application**: Service-specific metrics
4. **Business**: User activity and business metrics
5. **Security**: Security and compliance metrics

Each category contains multiple dashboards focusing on specific aspects of the system.

## System Dashboard

Key metrics:
- CPU, Memory, Disk, and Network usage
- Container health and resource usage
- System load and process count

![System Dashboard](../assets/images/system-dashboard.png)

Example PromQL queries:

```
# CPU Usage
sum(rate(node_cpu_seconds_total{mode!="idle"}[5m])) by (instance) / 
sum(rate(node_cpu_seconds_total[5m])) by (instance) * 100

# Memory Usage
(node_memory_MemTotal_bytes - node_memory_MemFree_bytes - node_memory_Buffers_bytes - node_memory_Cached_bytes) / 
node_memory_MemTotal_bytes * 100

# Disk Usage
(1 - node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100

# Network Traffic
sum(rate(node_network_receive_bytes_total[5m])) by (instance)
```

## Application Dashboard

Key metrics:
- Request rate and latency by endpoint
- Error rates and status code distribution
- Active users and session count
- Authentication success/failure rates

![Application Dashboard](../assets/images/application-dashboard.png)

Example PromQL queries:

```
# Request Rate
sum(rate(http_requests_total[5m])) by (endpoint)

# Response Time (95th percentile)
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint))

# Error Rate
sum(rate(http_requests_total{status_code=~"5.."}[5m])) / 
sum(rate(http_requests_total[5m])) * 100

# Active Users
sum(active_users)
```

## LLM Dashboard

Key metrics:
- Token usage by provider and model
- Response times by model
- Error rates by provider
- Cost tracking and projections

![LLM Dashboard](../assets/images/llm-dashboard.png)

Example PromQL queries:

```
# Token Usage
sum(rate(llm_tokens_total[24h])) by (provider, model, type)

# Response Time
avg(llm_response_time_seconds) by (provider, model)

# Error Rate
sum(rate(llm_requests_total{status="error"}[5m])) by (provider) / 
sum(rate(llm_requests_total[5m])) by (provider) * 100

# Estimated Cost
sum(increase(llm_cost_total[24h])) by (provider, model)
```

## Database Dashboard

Key metrics:
- Query performance and slow queries
- Connection pool utilization
- Transaction rate and duration
- Table sizes and growth rate

![Database Dashboard](../assets/images/database-dashboard.png)

Example PromQL queries:

```
# Connection Pool Usage
sum(pg_stat_activity_count) by (database) / 
sum(pg_settings_max_connections)

# Query Duration (95th percentile)
histogram_quantile(0.95, sum(rate(pg_stat_statements_seconds_bucket[5m])) by (le, query_id))

# Transaction Rate
sum(rate(pg_stat_database_xact_commit[5m]) + rate(pg_stat_database_xact_rollback[5m])) by (database)
```

## User Journey Dashboard

This dashboard provides insights into user experience and business metrics:

- Funnel visualization of user signup flow
- Colony creation and management statistics
- AI agent usage patterns
- User engagement metrics

Example visualization:

```javascript
// Funnel Panel Configuration in Grafana
{
  "title": "User Onboarding Flow",
  "type": "echart",
  "datasource": {
    "type": "prometheus",
    "uid": "${DS_PROMETHEUS}"
  },
  "options": {
    "series": [
      {
        "type": "funnel",
        "data": [
          {
            "name": "Website Visits",
            "value": "${VISIT_COUNT}"
          },
          {
            "name": "Signup Initiated",
            "value": "${SIGNUP_INITIATED}" 
          },
          {
            "name": "Account Created",
            "value": "${ACCOUNT_CREATED}"
          },
          {
            "name": "First Colony Created",
            "value": "${COLONY_CREATED}"
          },
          {
            "name": "First Agent Deployed",
            "value": "${AGENT_DEPLOYED}"
          }
        ]
      }
    ]
  }
}
```

## Executive Dashboard

A high-level dashboard designed for management and executives:

- System health and reliability metrics
- User growth and engagement trends
- Resource utilization and costs
- Key business metrics

This dashboard focuses on simplicity and clarity, with less technical detail and more business-oriented metrics.

## Dashboard Access Control

Dashboard access is controlled based on user roles:

1. **Admin**: Full access to all dashboards
2. **DevOps**: Full access to system and application dashboards
3. **Developer**: Read access to application dashboards
4. **Business Analyst**: Access to business and user journey dashboards
5. **Executive**: Access to executive dashboard only

## Dashboard Development Workflow

New dashboards and changes to existing dashboards follow a structured workflow:

1. **Development**: Created in a dev Grafana instance
2. **Version Control**: Dashboard JSON exported and stored in git
3. **Review**: Code review for dashboard changes
4. **Deployment**: Automated deployment to production through CI/CD
5. **Documentation**: Dashboards are documented with description and usage guidelines

Dashboard JSON template:

```json
{
  "annotations": {
    "list": [
      {
        "builtIn": 1,
        "datasource": "-- Grafana --",
        "enable": true,
        "hide": true,
        "iconColor": "rgba(0, 211, 255, 1)",
        "name": "Deployments",
        "type": "dashboard"
      }
    ]
  },
  "editable": true,
  "gnetId": null,
  "graphTooltip": 0,
  "id": null,
  "links": [],
  "panels": [
    {
      "title": "Request Rate",
      "type": "graph",
      "datasource": "${DS_PROMETHEUS}",
      "targets": [
        {
          "expr": "sum(rate(http_requests_total[5m])) by (endpoint)",
          "legendFormat": "{{endpoint}}"
        }
      ]
    }
  ],
  "templating": {
    "list": [
      {
        "name": "environment",
        "type": "custom",
        "options": [
          {
            "text": "production",
            "value": "production"
          },
          {
            "text": "staging",
            "value": "staging"
          }
        ],
        "current": {
          "text": "production",
          "value": "production"
        }
      }
    ]
  },
  "time": {
    "from": "now-6h",
    "to": "now"
  },
  "version": 1
}
```
