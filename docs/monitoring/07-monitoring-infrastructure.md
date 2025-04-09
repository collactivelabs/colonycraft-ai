# Monitoring Infrastructure

## Components

The ColonyCraft AI monitoring stack consists of the following components:

1. **Prometheus**: Central metrics collection and storage
2. **Grafana**: Visualization and dashboarding
3. **OpenTelemetry Collector**: Distributed tracing collection
4. **ELK Stack**: Log aggregation and analysis
   - Elasticsearch: Log storage and search
   - Logstash: Log processing pipeline
   - Kibana: Log visualization and exploration
5. **Alertmanager**: Alert routing and notification
6. **Node Exporter**: System metrics collection
7. **cAdvisor**: Container metrics collection

## Deployment Architecture

The monitoring stack is deployed alongside the application with high availability:

```
                           ┌────────────┐
                           │            │
                           │  Grafana   │
                           │            │
                           └─────┬──────┘
                                 │
                                 ▼
┌──────────────┐          ┌────────────┐          ┌──────────────┐
│              │          │            │          │              │
│ Alertmanager ├──────────┤ Prometheus ├──────────┤ OpenTelemetry│
│              │          │            │          │              │
└──────┬───────┘          └─────┬──────┘          └──────┬───────┘
       │                        │                        │
       │                        │                        │
       ▼                        ▼                        ▼
┌──────────────┐          ┌────────────┐          ┌──────────────┐
│              │          │            │          │              │
│ PagerDuty    │          │ Exporters  │          │ ELK Stack    │
│ Slack, Email │          │            │          │              │
└──────────────┘          └────────────┘          └──────────────┘
```

## High Availability Considerations

1. **Prometheus**: Multiple replicas with Thanos for long-term storage
2. **Alertmanager**: Clustered for redundancy
3. **Grafana**: Multiple instances behind load balancer
4. **ELK Stack**: Clustered for high availability
5. **Backup**: Regular backups of configurations and data

## Kubernetes Deployment

The monitoring infrastructure is deployed in Kubernetes using Helm charts:

```yaml
# prometheus-values.yaml
prometheus:
  replicaCount: 2
  retention: 15d
  resources:
    requests:
      cpu: 1
      memory: 8Gi
    limits:
      cpu: 2
      memory: 16Gi
  
  persistentVolume:
    size: 100Gi
    storageClass: ssd
  
  serviceMonitors:
    - name: api-services
      selector:
        matchLabels:
          app: api
      endpoints:
        - port: http
          interval: 15s
          path: /metrics

alertmanager:
  replicaCount: 3
  config:
    global:
      resolve_timeout: 5m
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
    receivers:
    - name: 'pagerduty-critical'
      pagerduty_configs:
      - service_key: '${PAGERDUTY_KEY}'
    - name: 'slack-notifications'
      slack_configs:
      - channel: '#monitoring'
        api_url: '${SLACK_WEBHOOK_URL}'
```

## Prometheus Configuration

Prometheus is configured to scrape metrics from all services:

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
    - role: pod
    relabel_configs:
    - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
      action: keep
      regex: true
    - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
      action: replace
      target_label: __metrics_path__
      regex: (.+)
    - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
      action: replace
      regex: (.+):(?:\d+);(\d+)
      replacement: ${1}:${2}
      target_label: __address__
    - action: labelmap
      regex: __meta_kubernetes_pod_label_(.+)
    - source_labels: [__meta_kubernetes_namespace]
      action: replace
      target_label: kubernetes_namespace
    - source_labels: [__meta_kubernetes_pod_name]
      action: replace
      target_label: kubernetes_pod_name

  - job_name: 'node-exporter'
    kubernetes_sd_configs:
    - role: node
    relabel_configs:
    - action: labelmap
      regex: __meta_kubernetes_node_label_(.+)
    - target_label: __address__
      replacement: kubernetes.default.svc:443
    - source_labels: [__meta_kubernetes_node_name]
      regex: (.+)
      target_label: __metrics_path__
      replacement: /api/v1/nodes/${1}/proxy/metrics
```

## Thanos for Long-Term Storage

Thanos is used to provide long-term storage for Prometheus metrics:

```yaml
# thanos-values.yaml
query:
  replicaCount: 2
  serviceAccount:
    create: true
  stores:
    - dnssrv+_grpc._tcp.thanos-store-gateway.monitoring.svc

compactor:
  enabled: true
  retention: 1y
  persistence:
    size: 100Gi

storegateway:
  replicaCount: 2
  persistence:
    size: 500Gi

bucketweb:
  enabled: true

objectStore:
  type: S3
  config:
    bucket: thanos-metrics
    endpoint: s3.amazonaws.com
    region: us-west-2
    access_key: ${AWS_ACCESS_KEY}
    secret_key: ${AWS_SECRET_KEY}
```

## OpenTelemetry Collector

The OpenTelemetry Collector is configured to collect and process traces:

```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 1s
    send_batch_size: 1000
  memory_limiter:
    check_interval: 1s
    limit_mib: 1000
  resourcedetection:
    detectors: [env, kubernetes]
  k8s_attributes:
    auth_type: "serviceAccount"
    passthrough: false
    extract:
      metadata:
        - k8s.pod.name
        - k8s.pod.uid
        - k8s.deployment.name
        - k8s.namespace.name
        - k8s.node.name
        - k8s.container.name

exporters:
  jaeger:
    endpoint: jaeger-collector:14250
    tls:
      insecure: true
  prometheus:
    endpoint: 0.0.0.0:8889
  logging:
    loglevel: info

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch, resourcedetection, k8s_attributes]
      exporters: [jaeger, logging]
    metrics:
      receivers: [otlp]
      processors: [memory_limiter, batch, resourcedetection, k8s_attributes]
      exporters: [prometheus, logging]
```

## ELK Stack Configuration

The ELK Stack is deployed with the following configuration:

```yaml
# elastic-values.yaml
elasticsearch:
  replicas: 3
  minimumMasterNodes: 2
  resources:
    requests:
      cpu: 1
      memory: 4Gi
    limits:
      cpu: 2
      memory: 8Gi
  volumeClaimTemplate:
    accessModes: ["ReadWriteOnce"]
    resources:
      requests:
        storage: 100Gi
  esConfig:
    elasticsearch.yml: |
      xpack.security.enabled: true
      xpack.monitoring.collection.enabled: true
      xpack.security.audit.enabled: true

logstash:
  replicas: 2
  resources:
    requests:
      cpu: 500m
      memory: 1Gi
    limits:
      cpu: 1
      memory: 2Gi
  persistence:
    enabled: true
    size: 20Gi
  logstashConfig:
    logstash.yml: |
      http.host: 0.0.0.0
      config.reload.automatic: true
      config.reload.interval: 30s
  logstashPipeline:
    logstash.conf: |
      input {
        beats {
          port => 5044
        }
        kafka {
          bootstrap_servers => "kafka:9092"
          topics => ["logs"]
          codec => "json"
        }
      }
      
      filter {
        json {
          source => "message"
        }
        date {
          match => ["timestamp", "ISO8601"]
          target => "@timestamp"
        }
      }
      
      output {
        elasticsearch {
          hosts => ["elasticsearch:9200"]
          index => "logs-%{+YYYY.MM.dd}"
          user => "${ELASTIC_USER}"
          password => "${ELASTIC_PASSWORD}"
        }
      }

kibana:
  replicas: 2
  resources:
    requests:
      cpu: 500m
      memory: 1Gi
    limits:
      cpu: 1
      memory: 2Gi
  kibanaConfig:
    kibana.yml: |
      server.name: kibana
      elasticsearch.hosts: ["http://elasticsearch:9200"]
      elasticsearch.username: "${ELASTIC_USER}"
      elasticsearch.password: "${ELASTIC_PASSWORD}"
      xpack.security.enabled: true
      xpack.monitoring.enabled: true
```

## Grafana Configuration

Grafana is configured with datasources and dashboards:

```yaml
# grafana-values.yaml
replicas: 2

persistence:
  enabled: true
  size: 10Gi

adminPassword: "${GRAFANA_ADMIN_PASSWORD}"

datasources:
  datasources.yaml:
    apiVersion: 1
    datasources:
    - name: Prometheus
      type: prometheus
      url: http://prometheus-server
      access: proxy
      isDefault: true
    - name: Elasticsearch
      type: elasticsearch
      url: http://elasticsearch:9200
      database: logs-*
      access: proxy
      basicAuth: true
      basicAuthUser: "${ELASTIC_USER}"
      basicAuthPassword: "${ELASTIC_PASSWORD}"
    - name: Jaeger
      type: jaeger
      url: http://jaeger-query:16686
      access: proxy

dashboardProviders:
  dashboardproviders.yaml:
    apiVersion: 1
    providers:
    - name: 'default'
      orgId: 1
      folder: ''
      type: file
      disableDeletion: false
      editable: true
      options:
        path: /var/lib/grafana/dashboards/default

dashboards:
  default:
    system-overview:
      json: |
        {
          "title": "System Overview",
          "uid": "system-overview",
          "version": 1,
          "panels": [
            {
              "title": "CPU Usage",
              "type": "graph",
              "gridPos": {"x": 0, "y": 0, "w": 12, "h": 8},
              "targets": [
                {
                  "expr": "sum(rate(node_cpu_seconds_total{mode!=\"idle\"}[5m])) by (instance) / sum(rate(node_cpu_seconds_total[5m])) by (instance) * 100",
                  "legendFormat": "{{instance}}"
                }
              ]
            }
          ]
        }
```

## Monitoring Network Design

The monitoring network is designed for security and performance:

1. **Segmentation**: Monitoring components are in a dedicated network segment
2. **Access Control**: Strict firewall rules limiting access to monitoring services
3. **Encryption**: TLS for all monitoring traffic
4. **Authentication**: mTLS for service-to-service communication

## Resource Requirements and Scaling

Resource allocation for monitoring components based on cluster size:

| Component | Small (< 10 nodes) | Medium (10-50 nodes) | Large (> 50 nodes) |
|-----------|--------------------|--------------------|------------------|
| Prometheus | 2 CPU, 8GB RAM, 100GB Storage | 4 CPU, 16GB RAM, 500GB Storage | 8 CPU, 32GB RAM, 1TB Storage |
| Elasticsearch | 3 nodes: 1 CPU, 4GB RAM each, 100GB Storage | 3 nodes: 2 CPU, 8GB RAM each, 500GB Storage | 5+ nodes: 4 CPU, 16GB RAM each, 1TB+ Storage |
| Grafana | 0.5 CPU, 1GB RAM | 1 CPU, 2GB RAM | 2 CPU, 4GB RAM |
| OpenTelemetry | 1 CPU, 2GB RAM | 2 CPU, 4GB RAM | 4 CPU, 8GB RAM |

Horizontal scaling is implemented for all components to handle increased load.
