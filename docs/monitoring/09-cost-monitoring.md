# Cost Monitoring

## LLM Usage Costs

Token usage is carefully tracked and associated with costs to provide visibility into LLM service expenses:

```python
# Track token costs
def track_token_costs(provider, model, input_tokens, output_tokens):
    # Pricing per 1000 tokens
    pricing = {
        "openai": {
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-32k": {"input": 0.06, "output": 0.12},
        },
        "anthropic": {
            "claude-instant": {"input": 0.0008, "output": 0.0024},
            "claude-2": {"input": 0.008, "output": 0.024},
        }
    }
    
    # Calculate costs
    if provider in pricing and model in pricing[provider]:
        input_cost = (input_tokens / 1000) * pricing[provider][model]["input"]
        output_cost = (output_tokens / 1000) * pricing[provider][model]["output"]
        total_cost = input_cost + output_cost
        
        # Track costs using Prometheus
        LLM_COST.labels(
            provider=provider,
            model=model,
            type="input"
        ).inc(input_cost)
        
        LLM_COST.labels(
            provider=provider,
            model=model,
            type="output"
        ).inc(output_cost)
        
        # Return costs for logging
        return {
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost
        }
    
    return None
```

## Infrastructure Cost Tracking

Infrastructure costs are tracked using the following approaches:

1. **Kubernetes Cost Allocation**: Tracking costs by namespace, deployment, and pod
2. **Cloud Resource Tagging**: Using consistent tagging for all cloud resources
3. **Resource Utilization**: Monitoring actual resource usage against provisioned resources

Example Kubernetes cost allocation:

```yaml
# kubecost configuration
kubecost:
  enabled: true
  
  networkCosts:
    enabled: true
  
  prometheus:
    enabled: false
    server: http://prometheus-server
  
  grafana:
    enabled: false
    domainName: grafana-service
  
  serviceMonitor:
    enabled: true
  
  cost-analyzer:
    extraEnv:
      - name: CLOUD_PROVIDER_API_KEY
        valueFrom:
          secretKeyRef:
            name: cloud-credentials
            key: api-key
```

## Cost Dashboards

Dedicated dashboards track costs by:

1. **User/Organization**: Usage and costs per user or organization
2. **Model**: Costs associated with each LLM model
3. **Time Period**: Daily, weekly, and monthly trends
4. **Budget Tracking**: Actual vs. budgeted costs with alerts

Example Grafana dashboard queries:

```
# Total cost by LLM provider
sum(increase(llm_cost_total[30d])) by (provider)

# Cost per user
sum(increase(llm_cost_total[30d])) by (user_id)

# Cost by model
sum(increase(llm_cost_total[30d])) by (model)

# Daily cost trend
sum(increase(llm_cost_total[1d])) by (day)
```

## Cost Optimization Strategies

The following strategies are employed to optimize costs:

1. **Caching**: Storing responses for common prompts
2. **Model Selection**: Using smaller models for simpler tasks
3. **Prompt Engineering**: Optimizing prompts to reduce token usage
4. **Budget Limits**: Enforcing usage caps by user or organization

### Caching Implementation

Response caching is implemented to avoid redundant LLM calls:

```python
import hashlib
import json
from redis import Redis
from datetime import timedelta

class LLMCache:
    def __init__(self, redis_client, ttl=timedelta(days=7)):
        self.redis = redis_client
        self.ttl = ttl
    
    def _generate_key(self, provider, model, prompt, options):
        """Generate a cache key based on request parameters"""
        cache_obj = {
            "provider": provider,
            "model": model,
            "prompt": prompt,
            "options": options
        }
        
        # Create a stable JSON string for hashing
        cache_str = json.dumps(cache_obj, sort_keys=True)
        return f"llm:cache:{hashlib.md5(cache_str.encode()).hexdigest()}"
    
    def get(self, provider, model, prompt, options):
        """Get cached response if available"""
        key = self._generate_key(provider, model, prompt, options)
        cached = self.redis.get(key)
        
        if cached:
            # Track cache hit
            CACHE_HITS.labels(provider=provider, model=model).inc()
            return json.loads(cached)
        
        # Track cache miss
        CACHE_MISSES.labels(provider=provider, model=model).inc()
        return None
    
    def set(self, provider, model, prompt, options, response):
        """Cache a response"""
        key = self._generate_key(provider, model, prompt, options)
        self.redis.setex(
            key, 
            int(self.ttl.total_seconds()),
            json.dumps(response)
        )
        
        # Track cache entry size
        CACHE_SIZE_BYTES.labels(provider=provider, model=model).inc(len(json.dumps(response)))
```

### Model Selection Logic

Intelligent model selection reduces costs by using the most appropriate model:

```python
def select_optimal_model(prompt, task_type, max_budget=None):
    """
    Select the most cost-effective model based on task requirements
    
    Args:
        prompt: User prompt
        task_type: Type of task (classification, generation, etc.)
        max_budget: Maximum cost allowed for this request
        
    Returns:
        Selected provider and model
    """
    prompt_length = len(prompt)
    estimated_tokens = len(prompt.split()) * 1.3  # Rough token estimate
    
    # Estimate output token count based on task type
    estimated_output_tokens = {
        "classification": 50,
        "generation": estimated_tokens * 1.5,
        "summarization": estimated_tokens * 0.5,
        "qa": estimated_tokens * 0.8,
    }.get(task_type, estimated_tokens)
    
    # Model capabilities and costs
    models = [
        {
            "provider": "openai",
            "model": "gpt-3.5-turbo",
            "capabilities": ["classification", "generation", "summarization", "qa"],
            "input_cost": 0.0015,  # per 1K tokens
            "output_cost": 0.002,   # per 1K tokens
            "quality": 0.8
        },
        {
            "provider": "openai",
            "model": "gpt-4",
            "capabilities": ["classification", "generation", "summarization", "qa"],
            "input_cost": 0.03,   # per 1K tokens
            "output_cost": 0.06,  # per 1K tokens
            "quality": 0.95
        },
        {
            "provider": "anthropic",
            "model": "claude-instant",
            "capabilities": ["classification", "generation", "summarization", "qa"],
            "input_cost": 0.0008,  # per 1K tokens
            "output_cost": 0.0024, # per 1K tokens
            "quality": 0.75
        }
    ]
    
    # Filter models suitable for task
    suitable_models = [m for m in models if task_type in m["capabilities"]]
    
    # Calculate estimated cost for each model
    for model in suitable_models:
        input_cost = (estimated_tokens / 1000) * model["input_cost"]
        output_cost = (estimated_output_tokens / 1000) * model["output_cost"]
        model["estimated_cost"] = input_cost + output_cost
    
    # If budget is specified, filter by budget
    if max_budget:
        suitable_models = [m for m in suitable_models if m["estimated_cost"] <= max_budget]
    
    # If no models fit the budget, return the cheapest option
    if not suitable_models:
        return min(models, key=lambda m: m["estimated_cost"])
    
    # Choose the model with the best quality/cost ratio
    for model in suitable_models:
        model["value_ratio"] = model["quality"] / model["estimated_cost"]
    
    selected = max(suitable_models, key=lambda m: m["value_ratio"])
    return {"provider": selected["provider"], "model": selected["model"]}
```

### Prompt Optimization

The system implements prompt optimization to reduce token usage:

```python
def optimize_prompt(prompt, context=None):
    """
    Optimize a prompt to reduce token usage while maintaining functionality
    
    Args:
        prompt: Original user prompt
        context: Additional context about the request
        
    Returns:
        Optimized prompt
    """
    # Remove redundant whitespace
    prompt = " ".join(prompt.split())
    
    # If system prompt is included, extract and optimize separately
    if "system:" in prompt.lower():
        parts = prompt.split("system:", 1)
        user_prompt = parts[0].strip()
        system_prompt = "system:" + parts[1].strip()
        
        # Optimize system prompt - remove unnecessary elements
        system_prompt = re.sub(r'you are .+?\.', '', system_prompt, flags=re.IGNORECASE)
        system_prompt = re.sub(r'please .+?\.', '', system_prompt, flags=re.IGNORECASE)
        
        # Combine optimized parts
        prompt = f"{user_prompt}\n\n{system_prompt}"
    
    # Replace verbose constructions with concise versions
    replacements = [
        (r"I would like you to", "Please"),
        (r"Can you please", "Please"),
        (r"I am interested in", "I need"),
        (r"It would be great if you could", "Please"),
        (r"I would appreciate it if you could", "Please"),
    ]
    
    for pattern, replacement in replacements:
        prompt = re.sub(pattern, replacement, prompt, flags=re.IGNORECASE)
    
    # If context is provided, only include relevant parts
    if context and "relevant_keywords" in context:
        keywords = context["relevant_keywords"]
        paragraphs = prompt.split("\n\n")
        
        # Score paragraphs by relevance
        scored_paragraphs = []
        for p in paragraphs:
            score = sum(1 for kw in keywords if kw.lower() in p.lower())
            scored_paragraphs.append((p, score))
        
        # Keep only the most relevant paragraphs
        scored_paragraphs.sort(key=lambda x: x[1], reverse=True)
        top_paragraphs = [p[0] for p in scored_paragraphs[:3]]
        
        prompt = "\n\n".join(top_paragraphs)
    
    return prompt
```

### Budget Enforcement

Usage limits are enforced to control costs:

```python
class BudgetManager:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def track_cost(self, user_id, organization_id, cost):
        """
        Track cost for a user and organization
        
        Args:
            user_id: User ID
            organization_id: Organization ID
            cost: Cost of the request
        """
        # Track monthly user cost
        user_key = f"cost:user:{user_id}:{datetime.now().strftime('%Y-%m')}"
        self.redis.incrbyfloat(user_key, cost)
        
        # Track monthly organization cost
        org_key = f"cost:org:{organization_id}:{datetime.now().strftime('%Y-%m')}"
        self.redis.incrbyfloat(org_key, cost)
        
        # Update daily metrics
        day_key = f"cost:daily:{datetime.now().strftime('%Y-%m-%d')}"
        self.redis.incrbyfloat(day_key, cost)
        
        # Update global metrics
        COST_TOTAL.inc(cost)
        USER_COSTS.labels(user_id=user_id).inc(cost)
        ORG_COSTS.labels(organization_id=organization_id).inc(cost)
    
    def check_budget(self, user_id, organization_id, estimated_cost):
        """
        Check if a request is within budget
        
        Args:
            user_id: User ID
            organization_id: Organization ID
            estimated_cost: Estimated cost of the request
            
        Returns:
            Boolean indicating if request is within budget
        """
        # Get user and organization budget information
        user_budget = self._get_user_budget(user_id)
        org_budget = self._get_org_budget(organization_id)
        
        # Get current spending
        user_key = f"cost:user:{user_id}:{datetime.now().strftime('%Y-%m')}"
        user_spent = float(self.redis.get(user_key) or 0)
        
        org_key = f"cost:org:{organization_id}:{datetime.now().strftime('%Y-%m')}"
        org_spent = float(self.redis.get(org_key) or 0)
        
        # Check if request would exceed any budgets
        if user_budget and user_spent + estimated_cost > user_budget:
            # Track budget exceeded events
            BUDGET_EXCEEDED.labels(entity_type="user", entity_id=user_id).inc()
            return False
        
        if org_budget and org_spent + estimated_cost > org_budget:
            # Track budget exceeded events
            BUDGET_EXCEEDED.labels(entity_type="organization", entity_id=organization_id).inc()
            return False
        
        return True
    
    def _get_user_budget(self, user_id):
        """Get user's monthly budget"""
        # This would typically come from a database
        # For now, we'll use a simple Redis lookup
        budget_key = f"budget:user:{user_id}"
        budget = self.redis.get(budget_key)
        return float(budget) if budget else None
    
    def _get_org_budget(self, organization_id):
        """Get organization's monthly budget"""
        # This would typically come from a database
        budget_key = f"budget:org:{organization_id}"
        budget = self.redis.get(budget_key)
        return float(budget) if budget else None
```

## Cost Forecasting

The system provides cost forecasting to predict future expenses:

```python
def forecast_monthly_costs(historical_data, forecast_months=3):
    """
    Forecast future costs based on historical data
    
    Args:
        historical_data: DataFrame with daily costs
        forecast_months: Number of months to forecast
        
    Returns:
        DataFrame with forecasted costs
    """
    # Prepare data for Prophet
    df = historical_data.rename(columns={"date": "ds", "cost": "y"})
    
    # Initialize and train model
    model = Prophet(
        daily_seasonality=False,
        weekly_seasonality=True,
        yearly_seasonality=True,
        seasonality_mode='multiplicative',
        changepoint_prior_scale=0.05
    )
    
    # Add monthly seasonality
    model.add_seasonality(
        name='monthly',
        period=30.5,
        fourier_order=5
    )
    
    # Add special events if relevant
    # model.add_country_holidays(country_name='US')
    
    # Fit the model
    model.fit(df)
    
    # Create future dataframe for forecasting
    future = model.make_future_dataframe(
        periods=forecast_months * 30,
        freq='D'
    )
    
    # Generate forecast
    forecast = model.predict(future)
    
    # Add monthly total
    forecast['month'] = forecast['ds'].dt.strftime('%Y-%m')
    monthly_forecast = forecast.groupby('month').agg({
        'yhat': 'sum',
        'yhat_lower': 'sum',
        'yhat_upper': 'sum'
    }).reset_index()
    
    return {
        'daily': forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']],
        'monthly': monthly_forecast
    }
```

## Chargeback and Cost Allocation

For enterprise environments, costs are allocated to specific departments or projects:

```python
def allocate_costs(monthly_costs):
    """
    Allocate costs to departments/cost centers
    
    Args:
        monthly_costs: Total monthly costs
        
    Returns:
        Cost allocation by department
    """
    # Get usage breakdown by department
    department_usage = db.query("""
        SELECT 
            d.name AS department,
            COUNT(DISTINCT u.id) AS users,
            SUM(r.token_count) AS tokens,
            SUM(r.cost) AS cost
        FROM 
            requests r
            JOIN users u ON r.user_id = u.id
            JOIN departments d ON u.department_id = d.id
        WHERE 
            r.timestamp >= DATE_TRUNC('month', CURRENT_DATE)
            AND r.timestamp < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
        GROUP BY 
            d.name
    """)
    
    # Calculate percentage breakdown
    total_cost = sum(d['cost'] for d in department_usage)
    
    for dept in department_usage:
        dept['percentage'] = (dept['cost'] / total_cost) * 100
        dept['allocated_cost'] = (dept['percentage'] / 100) * monthly_costs
    
    return department_usage
```

## Cost Optimization Analysis

The system provides recommendations for cost optimization:

```python
def generate_cost_optimization_recommendations():
    """
    Generate recommendations for cost optimization
    
    Returns:
        List of recommendations with potential savings
    """
    recommendations = []
    
    # Check for caching opportunities
    duplicate_queries = db.query("""
        SELECT 
            COUNT(*) as total_requests,
            COUNT(DISTINCT prompt_hash) as unique_prompts,
            SUM(cost) as total_cost
        FROM 
            requests
        WHERE 
            timestamp >= NOW() - INTERVAL '30 days'
    """)
    
    if duplicate_queries[0]['total_requests'] > duplicate_queries[0]['unique_prompts'] * 1.2:
        potential_savings = duplicate_queries[0]['total_cost'] * 0.2
        recommendations.append({
            'type': 'caching',
            'description': 'Implement response caching to reduce duplicate requests',
            'potential_savings': potential_savings
        })
    
    # Check for opportunities to use smaller models
    model_usage = db.query("""
        SELECT 
            model,
            COUNT(*) as requests,
            AVG(token_count) as avg_tokens,
            SUM(cost) as total_cost
        FROM 
            requests
        WHERE 
            timestamp >= NOW() - INTERVAL '30 days'
        GROUP BY 
            model
        ORDER BY 
            total_cost DESC
    """)
    
    # Identify simple requests that could use cheaper models
    for row in model_usage:
        if row['model'] == 'gpt-4' and row['avg_tokens'] < 500:
            potential_savings = row['total_cost'] * 0.7
            recommendations.append({
                'type': 'model_selection',
                'description': 'Use GPT-3.5 for simpler requests under 500 tokens',
                'potential_savings': potential_savings,
                'details': {
                    'current_model': 'gpt-4',
                    'recommended_model': 'gpt-3.5-turbo',
                    'affected_requests': row['requests']
                }
            })
    
    return recommendations
```
