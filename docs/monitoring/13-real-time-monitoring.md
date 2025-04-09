# Real-time Monitoring and Visualization

## Real-time Dashboards

ColonyCraft-AI requires real-time visibility into system performance and user activity. The following real-time dashboards are implemented:

1. **Operations Command Center**: A centralized, large-screen display for NOC (Network Operations Center) showing:
   - System health indicators
   - Active incidents and their status
   - Geographic distribution of active users
   - Resource utilization across regions

2. **User Activity Stream**: Real-time visualization of:
   - User sessions and interactions
   - Colony creation and modification events
   - AI agent deployment and activity
   - Resource consumption by colony

### Operations Command Center

The Operations Command Center dashboard is designed for large-screen displays in the operations center and provides a unified view of system health:

```javascript
// Dashboard panel configuration - System Health Overview
{
  "dashboard": {
    "id": "operations-command-center",
    "title": "Operations Command Center",
    "tags": ["operations", "realtime"],
    "refresh": "5s",
    "panels": [
      {
        "title": "System Health",
        "type": "gauge",
        "gridPos": {"x": 0, "y": 0, "w": 6, "h": 8},
        "options": {
          "reduceOptions": {
            "values": false,
            "calcs": ["lastNotNull"],
            "fields": ""
          },
          "orientation": "auto",
          "showThresholdLabels": false,
          "showThresholdMarkers": true,
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {"value": null, "color": "red"},
              {"value": 95, "color": "yellow"},
              {"value": 98, "color": "green"}
            ]
          }
        },
        "targets": [
          {
            "expr": "avg(up{job=~\".*\"})*100",
            "instant": true
          }
        ]
      },
      {
        "title": "Active Incidents",
        "type": "table",
        "gridPos": {"x": 6, "y": 0, "w": 12, "h": 8},
        "options": {
          "showHeader": true,
          "sortBy": [
            {
              "displayName": "Severity",
              "desc": true
            }
          ]
        },
        "targets": [
          {
            "expr": "ALERTS{alertstate=\"firing\"}",
            "instant": true,
            "format": "table"
          }
        ],
        "transformations": [
          {
            "id": "organize",
            "options": {
              "excludeByName": {
                "Time": true,
                "Value": true
              },
              "indexByName": {},
              "renameByName": {
                "alertname": "Alert",
                "severity": "Severity",
                "instance": "Instance",
                "job": "Service",
                "started_at": "Started At"
              }
            }
          }
        ]
      },
      {
        "title": "Global Request Rate",
        "type": "timeseries",
        "gridPos": {"x": 0, "y": 8, "w": 12, "h": 8},
        "options": {
          "legend": {"showLegend": true},
          "tooltip": {"mode": "single", "sort": "none"},
          "visualization": {"type": "line"}
        },
        "targets": [
          {
            "expr": "sum(rate(http_requests_total[1m]))",
            "legendFormat": "Requests/sec"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "timeseries",
        "gridPos": {"x": 12, "y": 8, "w": 12, "h": 8},
        "options": {
          "legend": {"showLegend": true},
          "tooltip": {"mode": "single", "sort": "none"},
          "visualization": {"type": "line"}
        },
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{status_code=~\"5..\"}[1m])) / sum(rate(http_requests_total[1m]))",
            "legendFormat": "Error Rate %"
          }
        ]
      },
      {
        "title": "Geographic User Distribution",
        "type": "geomap",
        "gridPos": {"x": 0, "y": 16, "w": 12, "h": 12},
        "options": {
          "basemap": {"type": "default"},
          "controls": {"showZoom": true, "showAttribution": true},
          "layers": [
            {
              "type": "markers",
              "config": {
                "showLegend": true,
                "size": {"fixed": 5, "max": 15, "min": 2, "field": "Value"},
                "color": {"fixed": "dark-green"}
              }
            }
          ],
          "view": {"id": "zero", "lat": 0, "lon": 0, "zoom": 1}
        },
        "targets": [
          {
            "expr": "sum(active_users) by (country_code, region)",
            "format": "table"
          }
        ]
      },
      {
        "title": "Resource Utilization by Region",
        "type": "barchart",
        "gridPos": {"x": 12, "y": 16, "w": 12, "h": 12},
        "options": {
          "orientation": "horizontal",
          "xField": "Value",
          "colorByField": "region",
          "text": {"valueField": "Value"}
        },
        "targets": [
          {
            "expr": "sum(container_cpu_usage_seconds_total) by (region)",
            "instant": true,
            "format": "table"
          }
        ]
      }
    ]
  }
}
```

### User Activity Stream

The User Activity Stream dashboard provides real-time visibility into user interactions and behavior:

```javascript
// Dashboard panel configuration - User Activity Stream
{
  "dashboard": {
    "id": "user-activity-stream",
    "title": "User Activity Stream",
    "tags": ["user", "activity", "realtime"],
    "refresh": "5s",
    "panels": [
      {
        "title": "Active Users",
        "type": "stat",
        "gridPos": {"x": 0, "y": 0, "w": 6, "h": 4},
        "options": {
          "colorMode": "value",
          "graphMode": "area",
          "justifyMode": "auto",
          "orientation": "auto",
          "reduceOptions": {
            "calcs": ["lastNotNull"],
            "fields": "",
            "values": false
          }
        },
        "targets": [
          {
            "expr": "sum(active_users)",
            "instant": false
          }
        ]
      },
      {
        "title": "Colonies Created (Last Hour)",
        "type": "stat",
        "gridPos": {"x": 6, "y": 0, "w": 6, "h": 4},
        "options": {
          "colorMode": "value",
          "graphMode": "area",
          "justifyMode": "auto",
          "orientation": "auto",
          "reduceOptions": {
            "calcs": ["lastNotNull"],
            "fields": "",
            "values": false
          }
        },
        "targets": [
          {
            "expr": "sum(increase(colony_created_total[1h]))",
            "instant": false
          }
        ]
      },
      {
        "title": "Agents Deployed (Last Hour)",
        "type": "stat",
        "gridPos": {"x": 12, "y": 0, "w": 6, "h": 4},
        "options": {
          "colorMode": "value",
          "graphMode": "area",
          "justifyMode": "auto",
          "orientation": "auto",
          "reduceOptions": {
            "calcs": ["lastNotNull"],
            "fields": "",
            "values": false
          }
        },
        "targets": [
          {
            "expr": "sum(increase(agent_deployed_total[1h]))",
            "instant": false
          }
        ]
      },
      {
        "title": "Token Usage (Last Hour)",
        "type": "stat",
        "gridPos": {"x": 18, "y": 0, "w": 6, "h": 4},
        "options": {
          "colorMode": "value",
          "graphMode": "area",
          "justifyMode": "auto",
          "orientation": "auto",
          "reduceOptions": {
            "calcs": ["lastNotNull"],
            "fields": "",
            "values": false
          }
        },
        "targets": [
          {
            "expr": "sum(increase(llm_tokens_total[1h]))",
            "instant": false
          }
        ]
      },
      {
        "title": "Activity Stream",
        "type": "logs",
        "gridPos": {"x": 0, "y": 4, "w": 24, "h": 8},
        "options": {
          "showTime": true,
          "showLabels": true,
          "showCommonLabels": false,
          "wrapLogMessage": true,
          "prettifyLogMessage": true,
          "enableLogDetails": true,
          "dedupStrategy": "none"
        },
        "targets": [
          {
            "expr": "{job=\"user-activity\"} |~ \".*\"",
            "refId": "A"
          }
        ]
      },
      {
        "title": "Active Sessions by Platform",
        "type": "piechart",
        "gridPos": {"x": 0, "y": 12, "w": 8, "h": 8},
        "options": {
          "pieType": "pie",
          "displayLabels": ["name", "percent"],
          "legend": {"displayMode": "list", "placement": "right", "values": ["percent", "value"]}
        },
        "targets": [
          {
            "expr": "sum(active_users) by (platform)",
            "instant": true
          }
        ]
      },
      {
        "title": "Session Duration (Last 24h)",
        "type": "histogram",
        "gridPos": {"x": 8, "y": 12, "w": 16, "h": 8},
        "options": {
          "bucketSize": 5,
          "bucketOffset": 0,
          "combine": true
        },
        "targets": [
          {
            "expr": "session_duration_minutes_bucket",
            "format": "heatmap"
          }
        ]
      },
      {
        "title": "Top Colonies by Activity",
        "type": "table",
        "gridPos": {"x": 0, "y": 20, "w": 12, "h": 8},
        "options": {
          "showHeader": true,
          "sortBy": [
            {
              "displayName": "Activity",
              "desc": true
            }
          ]
        },
        "targets": [
          {
            "expr": "topk(10, sum(colony_activity) by (colony_id, colony_name))",
            "instant": true,
            "format": "table"
          }
        ],
        "transformations": [
          {
            "id": "organize",
            "options": {
              "excludeByName": {
                "Time": true
              },
              "indexByName": {},
              "renameByName": {
                "colony_id": "ID",
                "colony_name": "Name",
                "Value": "Activity"
              }
            }
          }
        ]
      },
      {
        "title": "Top Users by Token Usage",
        "type": "table",
        "gridPos": {"x": 12, "y": 20, "w": 12, "h": 8},
        "options": {
          "showHeader": true,
          "sortBy": [
            {
              "displayName": "Tokens",
              "desc": true
            }
          ]
        },
        "targets": [
          {
            "expr": "topk(10, sum(increase(user_token_usage_total[24h])) by (user_id, username))",
            "instant": true,
            "format": "table"
          }
        ],
        "transformations": [
          {
            "id": "organize",
            "options": {
              "excludeByName": {
                "Time": true
              },
              "indexByName": {},
              "renameByName": {
                "user_id": "ID",
                "username": "Username",
                "Value": "Tokens"
              }
            }
          }
        ]
      }
    ]
  }
}
```

## Time-Series Visualization

Effective visualization of time-series data is achieved using:

1. **Grafana Heatmaps**: For displaying distribution of metrics:
   - Response time distributions
   - User activity patterns
   - Resource utilization patterns

2. **Flame Graphs**: For visualizing:
   - API call stack performance
   - Resource consumption hierarchy 
   - Bottleneck identification

```yaml
# Example Grafana dashboard config snippet
panels:
  - title: "Response Time Heatmap"
    type: "heatmap"
    datasource: "Prometheus"
    targets:
      - expr: "sum(rate(http_request_duration_seconds_bucket[5m])) by (le)"
        format: "heatmap"
    heatmap:
      color:
        mode: "scheme"
        scheme: "RdYlGn"
      cards:
        cardPadding: 1
        cardRound: 0
      yBucketBound: "auto"
      reverseYBuckets: false
      hideZeroBuckets: true
```

3. **PromQL for Advanced Visualizations**:

```
# Apdex score (application performance index)
(
  sum(rate(http_request_duration_seconds_bucket{le="0.3"}[5m]))
  +
  sum(rate(http_request_duration_seconds_bucket{le="1.2"}[5m])) / 2
) / sum(rate(http_request_duration_seconds_count[5m]))
```

## Real-time Event Processing

The real-time monitoring system includes event processing capabilities:

1. **Event Stream**: Kafka stream for real-time event processing
2. **Stream Processing**: Flink jobs for event aggregation and analysis
3. **Event Correlation**: Correlating events across services
4. **Alert Generation**: Generating alerts based on event patterns

```java
// Example Flink job for processing user activity events
public class UserActivityProcessor extends FlinkKafkaConsumer<String> {
    
    public static void main(String[] args) throws Exception {
        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
        
        // Configure Kafka consumer
        Properties properties = new Properties();
        properties.setProperty("bootstrap.servers", "kafka:9092");
        properties.setProperty("group.id", "user-activity-processor");
        
        // Create Kafka consumer for user activity events
        FlinkKafkaConsumer<String> consumer = new FlinkKafkaConsumer<>(
            "user-activity",
            new SimpleStringSchema(),
            properties
        );
        
        // Configure the consumer to start from the latest record
        consumer.setStartFromLatest();
        
        // Create a stream of user activity events
        DataStream<UserActivityEvent> userActivityStream = env
            .addSource(consumer)
            .map(json -> parseUserActivityEvent(json));
        
        // Compute active users within 5-minute windows
        userActivityStream
            .map(event -> new Tuple2<>(event.getUserId(), 1))
            .keyBy(0)  // Key by user ID
            .window(TumblingProcessingTimeWindows.of(Time.minutes(5)))
            .sum(1)    // Count events per user
            .map(tuple -> new ActiveUserCount(tuple.f0, tuple.f1))
            .addSink(new PrometheusExporterSink());
        
        // Compute top colonies by activity
        userActivityStream
            .filter(event -> event.getColonyId() != null)
            .map(event -> new Tuple2<>(event.getColonyId(), 1))
            .keyBy(0)  // Key by colony ID
            .window(TumblingProcessingTimeWindows.of(Time.minutes(5)))
            .sum(1)    // Count events per colony
            .map(tuple -> new ColonyActivityCount(tuple.f0, tuple.f1))
            .addSink(new PrometheusExporterSink());
        
        env.execute("User Activity Processor");
    }
    
    private static UserActivityEvent parseUserActivityEvent(String json) {
        // Parse JSON into UserActivityEvent object
        ObjectMapper mapper = new ObjectMapper();
        return mapper.readValue(json, UserActivityEvent.class);
    }
}

// PrometheusExporterSink for exporting metrics to Prometheus
public class PrometheusExporterSink<T> implements SinkFunction<T> {
    @Override
    public void invoke(T value, Context context) {
        if (value instanceof ActiveUserCount) {
            ActiveUserCount count = (ActiveUserCount) value;
            // Update Prometheus gauge for active users
            ACTIVE_USERS.labels(count.getUserId()).set(count.getCount());
        } else if (value instanceof ColonyActivityCount) {
            ColonyActivityCount count = (ColonyActivityCount) value;
            // Update Prometheus gauge for colony activity
            COLONY_ACTIVITY.labels(count.getColonyId()).set(count.getCount());
        }
    }
}
```

## Push-based Monitoring

In addition to pull-based metrics collection with Prometheus, the system implements push-based monitoring for real-time visibility:

1. **WebSocket Streaming**: Real-time metrics streamed via WebSockets
2. **Server-Sent Events**: Event streams for dashboard updates
3. **Push Gateway**: Prometheus Push Gateway for batch jobs
4. **Client-side Reporting**: Metrics reported from frontend applications

```javascript
// Client-side WebSocket connection for real-time metric updates
class MetricStreamClient {
    constructor(url) {
        this.url = url;
        this.socket = null;
        this.listeners = new Map();
        this.reconnectDelay = 1000;
        this.maxReconnectDelay = 30000;
    }
    
    connect() {
        console.log(`Connecting to metric stream at ${this.url}`);
        this.socket = new WebSocket(this.url);
        
        this.socket.onopen = () => {
            console.log("Connection established");
            this.reconnectDelay = 1000;
        };
        
        this.socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.dispatchMetric(data);
            } catch (e) {
                console.error("Error parsing metric data", e);
            }
        };
        
        this.socket.onclose = () => {
            console.log("Connection closed, reconnecting...");
            setTimeout(() => this.connect(), this.reconnectDelay);
            this.reconnectDelay = Math.min(this.reconnectDelay * 1.5, this.maxReconnectDelay);
        };
        
        this.socket.onerror = (error) => {
            console.error("WebSocket error", error);
            this.socket.close();
        };
    }
    
    subscribe(metricName, callback) {
        if (!this.listeners.has(metricName)) {
            this.listeners.set(metricName, []);
        }
        this.listeners.get(metricName).push(callback);
        
        // Request the metric if connection is open
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({
                action: "subscribe",
                metric: metricName
            }));
        }
    }
    
    unsubscribe(metricName, callback) {
        if (this.listeners.has(metricName)) {
            const callbacks = this.listeners.get(metricName);
            const index = callbacks.indexOf(callback);
            if (index !== -1) {
                callbacks.splice(index, 1);
                
                // If no more listeners, unsubscribe from the metric
                if (callbacks.length === 0) {
                    this.listeners.delete(metricName);
                    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                        this.socket.send(JSON.stringify({
                            action: "unsubscribe",
                            metric: metricName
                        }));
                    }
                }
            }
        }
    }
    
    dispatchMetric(data) {
        if (data.metric && this.listeners.has(data.metric)) {
            const callbacks = this.listeners.get(data.metric);
            callbacks.forEach(callback => callback(data.value, data.timestamp));
        }
    }
}

// Usage in dashboard components
const metricStream = new MetricStreamClient("wss://metrics.colonycraft.ai/stream");
metricStream.connect();

// Subscribe to active users metric
metricStream.subscribe("active_users", (value, timestamp) => {
    document.getElementById("active-users-count").innerText = value;
    updateChart("active-users-chart", value, timestamp);
});

// Subscribe to request rate metric
metricStream.subscribe("request_rate", (value, timestamp) => {
    document.getElementById("request-rate-value").innerText = value.toFixed(2);
    updateChart("request-rate-chart", value, timestamp);
});
```

## Data Visualization Best Practices

The real-time monitoring system follows these visualization best practices:

1. **Consistency**: Consistent color schemes and visual language
2. **Context**: Providing context with historical data and thresholds
3. **Focus**: Highlighting important information and alerts
4. **Interactivity**: Allowing drill-down for detailed investigation
5. **Clarity**: Clear and concise visual representation of data

### Color Schemes

The dashboard color scheme is designed to be intuitive and accessible:

- **Green**: Healthy, normal state
- **Yellow/Orange**: Warning, potential issue
- **Red**: Critical, requires immediate attention
- **Blue**: Informational, neutral metrics
- **Purple**: User activity and behavior

All colors are selected to be distinguishable by colorblind users, with additional shape and pattern indicators where necessary.

### Dashboard Hierarchy

Dashboards are organized in a hierarchical structure:

1. **Overview**: High-level system health and KPIs
2. **Domain-specific**: Focused views for specific system components
3. **Drill-down**: Detailed views for investigation
4. **Custom**: User-created views for specific needs

## Real-time Notification System

The real-time monitoring system includes a notification system for alerting users to important events:

1. **In-app Notifications**: Alerts displayed within the application UI
2. **Desktop Notifications**: System notifications for critical alerts
3. **Mobile Notifications**: Push notifications for on-the-go monitoring
4. **Email Digests**: Scheduled summaries of system performance

```typescript
// TypeScript notification service
interface Notification {
    id: string;
    type: 'info' | 'warning' | 'critical';
    title: string;
    message: string;
    timestamp: number;
    source: string;
    context?: Record<string, any>;
    actionUrl?: string;
}

class NotificationService {
    private static instance: NotificationService;
    private socket: WebSocket | null = null;
    private listeners: ((notification: Notification) => void)[] = [];
    
    private constructor() {
        this.connect();
    }
    
    public static getInstance(): NotificationService {
        if (!NotificationService.instance) {
            NotificationService.instance = new NotificationService();
        }
        
        return NotificationService.instance;
    }
    
    private connect(): void {
        this.socket = new WebSocket('wss://notifications.colonycraft.ai/stream');
        
        this.socket.onopen = () => {
            console.log('Notification stream connected');
        };
        
        this.socket.onmessage = (event) => {
            try {
                const notification: Notification = JSON.parse(event.data);
                this.notifyListeners(notification);
                
                // Show desktop notification for critical alerts if supported
                if (notification.type === 'critical' && 'Notification' in window) {
                    this.showDesktopNotification(notification);
                }
            } catch (error) {
                console.error('Error processing notification', error);
            }
        };
        
        this.socket.onclose = () => {
            console.log('Notification stream disconnected, reconnecting...');
            setTimeout(() => this.connect(), 5000);
        };
        
        this.socket.onerror = (error) => {
            console.error('WebSocket error', error);
            this.socket?.close();
        };
    }
    
    public addListener(listener: (notification: Notification) => void): void {
        this.listeners.push(listener);
    }
    
    public removeListener(listener: (notification: Notification) => void): void {
        const index = this.listeners.indexOf(listener);
        if (index !== -1) {
            this.listeners.splice(index, 1);
        }
    }
    
    private notifyListeners(notification: Notification): void {
        this.listeners.forEach(listener => listener(notification));
    }
    
    private showDesktopNotification(notification: Notification): void {
        if (Notification.permission === 'granted') {
            new Notification(notification.title, {
                body: notification.message,
                icon: `/assets/icons/${notification.type}.png`,
                tag: notification.id
            });
        } else if (Notification.permission !== 'denied') {
            Notification.requestPermission().then(permission => {
                if (permission === 'granted') {
                    this.showDesktopNotification(notification);
                }
            });
        }
    }
}

// Usage in application
const notificationService = NotificationService.getInstance();

notificationService.addListener((notification) => {
    // Update notification center
    const notificationCenter = document.getElementById('notification-center');
    const notificationElement = document.createElement('div');
    notificationElement.className = `notification ${notification.type}`;
    notificationElement.innerHTML = `
        <div class="notification-header">
            <span class="notification-title">${notification.title}</span>
            <span class="notification-time">${formatTime(notification.timestamp)}</span>
        </div>
        <div class="notification-message">${notification.message}</div>
        ${notification.actionUrl ? `<a href="${notification.actionUrl}" class="notification-action">View Details</a>` : ''}
    `;
    
    notificationCenter?.appendChild(notificationElement);
    
    // Show notification badge
    updateNotificationBadge();
});
```

## Mobile Monitoring Solutions

The real-time monitoring system extends to mobile platforms for on-the-go monitoring:

1. **Responsive Dashboards**: Mobile-optimized views of key metrics
2. **Native Apps**: Dedicated mobile applications for iOS and Android
3. **Push Notifications**: Critical alerts delivered to mobile devices
4. **Offline Access**: Cached data for reviewing metrics without connectivity

### Mobile Dashboard Design

Mobile dashboards focus on the most critical metrics and are designed for touch interaction:

1. **Simplified Views**: Focused on essential metrics
2. **Touch-friendly**: Large touch targets and swipe gestures
3. **Bandwidth Efficient**: Optimized data transfer for mobile networks
4. **Battery Aware**: Reduced update frequency when on battery power

## Conclusion

Real-time monitoring and visualization are essential components of the ColonyCraft AI monitoring and observability strategy. By providing immediate visibility into system performance and user behavior, the real-time monitoring system enables rapid detection and response to issues, ensuring a reliable and performant platform.

The combination of pull-based metrics collection with Prometheus and push-based real-time updates via WebSockets provides a comprehensive view of the system, while carefully designed dashboards make the information accessible and actionable for operations staff.
