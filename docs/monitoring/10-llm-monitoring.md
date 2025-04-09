# LLM-Specific Monitoring

## LLM-Specific Metrics

The ColonyCraft AI platform tracks specialized metrics for LLM services:

1. **Semantic Success Rate**: Percentage of responses that semantically address the prompt
2. **Hallucination Rate**: Detected instances of model hallucinations
3. **Response Diversity**: Variety in model responses for similar prompts
4. **Instruction Following**: How well models follow specific instructions

## Evaluation Pipeline

Automatic evaluation of LLM outputs is implemented through a dedicated pipeline:

```python
async def evaluate_llm_response(prompt, response, model):
    """
    Evaluate LLM response quality
    
    Args:
        prompt: User prompt
        response: LLM response
        model: Model used for generation
        
    Returns:
        Evaluation metrics
    """
    # Use evaluation model to assess response
    evaluation_prompt = f"""
    Evaluate the following AI response to a user prompt.
    
    USER PROMPT: {prompt}
    
    AI RESPONSE: {response}
    
    Rate the response on the following criteria on a scale of 1-5:
    1. Relevance: How directly does it address the prompt?
    2. Accuracy: Is the information correct and reliable?
    3. Completeness: Does it fully answer what was asked?
    4. Clarity: Is it easy to understand?
    5. Hallucinations: Does it contain made-up information? (1=many, 5=none)
    
    Output only a JSON object with numerical ratings.
    """
    
    # Call evaluation model
    try:
        evaluation_service = LLMServiceFactory.get_service("openai")
        evaluation_response = await evaluation_service.generate_response(
            prompt=evaluation_prompt,
            options={"model": "gpt-4"}
        )
        
        # Parse JSON response
        import json
        metrics = json.loads(evaluation_response.text)
        
        # Track metrics
        for criterion, score in metrics.items():
            LLM_QUALITY.labels(
                model=model,
                criterion=criterion
            ).observe(score)
        
        return metrics
    except Exception as e:
        logger.error(f"Failed to evaluate response: {str(e)}")
        return None
```

## Hallucination Detection

Specialized detection of hallucinations in LLM responses:

```python
def detect_hallucinations(prompt, response, reference_data=None):
    """
    Detect potential hallucinations in LLM responses
    
    Args:
        prompt: User prompt
        response: LLM response
        reference_data: Optional reference data to check against
        
    Returns:
        Dict with hallucination assessment
    """
    hallucination_types = []
    confidence = 0.0
    
    # Simple check for factual claims
    factual_claim_patterns = [
        r"In (\d{4}),",
        r"(\d{1,2})(?:st|nd|rd|th) century",
        r"According to (research|studies|data)",
        r"([\w\s]+) was born in (\d{4})",
        r"([\w\s]+) discovered ([\w\s]+) in (\d{4})"
    ]
    
    factual_claims = []
    for pattern in factual_claim_patterns:
        matches = re.finditer(pattern, response)
        for match in matches:
            factual_claims.append(match.group(0))
    
    # If we have reference data, check claims against it
    if reference_data and factual_claims:
        verified_claims = 0
        for claim in factual_claims:
            # Simple string matching - in production, use more sophisticated NLP
            if any(claim.lower() in ref.lower() for ref in reference_data):
                verified_claims += 1
        
        if verified_claims < len(factual_claims):
            hallucination_types.append("unverified_factual_claims")
            confidence = 0.7 * (len(factual_claims) - verified_claims) / len(factual_claims)
    
    # Check for logical inconsistencies
    contradictions = detect_contradictions(response)
    if contradictions:
        hallucination_types.append("logical_contradictions")
        confidence = max(confidence, 0.8)
    
    # Check if response contains information not related to prompt
    relevance_score = assess_relevance(prompt, response)
    if relevance_score < 0.6:
        hallucination_types.append("irrelevant_content")
        confidence = max(confidence, 0.6)
    
    return {
        "contains_hallucinations": len(hallucination_types) > 0,
        "hallucination_types": hallucination_types,
        "confidence": confidence,
        "factual_claims": factual_claims
    }

def detect_contradictions(text):
    """Detect logical contradictions in text"""
    # This is a simplified implementation
    # In production, use more sophisticated NLP techniques
    contradictions = []
    
    contradiction_patterns = [
        (r"([\w\s]+) is ([\w\s]+)", r"([\w\s]+) is not ([\w\s]+)"),
        (r"([\w\s]+) can ([\w\s]+)", r"([\w\s]+) cannot ([\w\s]+)"),
        (r"([\w\s]+) will ([\w\s]+)", r"([\w\s]+) will not ([\w\s]+)")
    ]
    
    for pattern_a, pattern_b in contradiction_patterns:
        matches_a = re.finditer(pattern_a, text)
        for match_a in matches_a:
            subject_a = match_a.group(1).strip()
            predicate_a = match_a.group(2).strip()
            
            # Look for contradicting statements
            matches_b = re.finditer(pattern_b, text)
            for match_b in matches_b:
                subject_b = match_b.group(1).strip()
                predicate_b = match_b.group(2).strip()
                
                if similar_strings(subject_a, subject_b) and similar_strings(predicate_a, predicate_b):
                    contradictions.append((match_a.group(0), match_b.group(0)))
    
    return contradictions

def assess_relevance(prompt, response):
    """Assess the relevance of the response to the prompt"""
    # This is a simplified implementation
    # In production, use embedding similarity or more sophisticated NLP
    
    # Extract key terms from prompt
    prompt_terms = set(re.findall(r'\b\w{3,}\b', prompt.lower()))
    
    # Extract key terms from response
    response_terms = set(re.findall(r'\b\w{3,}\b', response.lower()))
    
    # Calculate Jaccard similarity
    if not prompt_terms or not response_terms:
        return 0.5
    
    intersection = len(prompt_terms.intersection(response_terms))
    union = len(prompt_terms.union(response_terms))
    
    return intersection / union

def similar_strings(a, b, threshold=0.8):
    """Check if strings are similar using Levenshtein distance"""
    # Production version would use more sophisticated similarity metrics
    from difflib import SequenceMatcher
    return SequenceMatcher(None, a, b).ratio() > threshold
```

## Response Quality Metrics

The system tracks detailed response quality metrics:

1. **Response Time**: Time taken to generate responses
2. **Token Efficiency**: Ratio of output tokens to input tokens
3. **Completion Rate**: Percentage of responses that complete without truncation
4. **Error Analysis**: Categorization and tracking of failure modes

```python
class LLMMetricsTracker:
    def __init__(self):
        # Define Prometheus metrics
        self.response_time = Histogram(
            'llm_response_time_seconds',
            'LLM Response Time in Seconds',
            ['provider', 'model']
        )
        self.token_efficiency = Histogram(
            'llm_token_efficiency',
            'Ratio of Output Tokens to Input Tokens',
            ['provider', 'model']
        )
        self.completion_rate = Counter(
            'llm_completion_total',
            'LLM Response Completion Status',
            ['provider', 'model', 'status']
        )
        self.error_count = Counter(
            'llm_error_total',
            'LLM Response Errors',
            ['provider', 'model', 'error_type']
        )
        self.quality_score = Histogram(
            'llm_quality_score',
            'LLM Response Quality Score',
            ['provider', 'model', 'criterion']
        )
    
    def track_response(self, provider, model, input_tokens, output_tokens, 
                      response_time, is_complete, error=None):
        """Track metrics for an LLM response"""
        # Track response time
        self.response_time.labels(
            provider=provider,
            model=model
        ).observe(response_time)
        
        # Track token efficiency
        if input_tokens > 0:
            efficiency = output_tokens / input_tokens
            self.token_efficiency.labels(
                provider=provider,
                model=model
            ).observe(efficiency)
        
        # Track completion status
        status = "complete" if is_complete else "truncated"
        self.completion_rate.labels(
            provider=provider,
            model=model,
            status=status
        ).inc()
        
        # Track errors if any
        if error:
            error_type = categorize_error(error)
            self.error_count.labels(
                provider=provider,
                model=model,
                error_type=error_type
            ).inc()
    
    def track_quality(self, provider, model, quality_metrics):
        """Track quality metrics for an LLM response"""
        for criterion, score in quality_metrics.items():
            self.quality_score.labels(
                provider=provider,
                model=model,
                criterion=criterion
            ).observe(score)

def categorize_error(error):
    """Categorize LLM errors for monitoring"""
    error_str = str(error).lower()
    
    if "timeout" in error_str:
        return "timeout"
    elif "rate limit" in error_str:
        return "rate_limit"
    elif "context length" in error_str or "token limit" in error_str:
        return "context_length"
    elif "content filter" in error_str or "moderation" in error_str:
        return "content_policy"
    elif "authentication" in error_str or "auth" in error_str:
        return "authentication"
    elif "server" in error_str:
        return "server_error"
    elif "network" in error_str or "connection" in error_str:
        return "network"
    else:
        return "other"
```

## LLM Performance Dashboard

A dedicated dashboard monitors LLM performance:

```yaml
# Dashboard configuration snippet
dashboard:
  title: "LLM Performance Dashboard"
  uid: "llm-performance"
  tags: ["llm", "ai", "performance"]
  rows:
    - title: "Response Time and Throughput"
      panels:
        - title: "Response Time by Model (P95)"
          type: "graph"
          targets:
            - expr: "histogram_quantile(0.95, sum(rate(llm_response_time_seconds_bucket[5m])) by (le, model))"
              legendFormat: "{{model}}"
        - title: "Requests per Minute by Model"
          type: "graph"
          targets:
            - expr: "sum(rate(llm_requests_total[5m])) by (model) * 60"
              legendFormat: "{{model}}"
    
    - title: "Token Usage and Efficiency"
      panels:
        - title: "Token Usage by Model"
          type: "graph"
          targets:
            - expr: "sum(rate(llm_tokens_total[5m])) by (model, type)"
              legendFormat: "{{model}} - {{type}}"
        - title: "Token Efficiency Ratio"
          type: "graph"
          targets:
            - expr: "sum(rate(llm_tokens_total{type='output'}[5m])) by (model) / sum(rate(llm_tokens_total{type='input'}[5m])) by (model)"
              legendFormat: "{{model}}"
    
    - title: "Quality Metrics"
      panels:
        - title: "Quality Score by Criterion"
          type: "heatmap"
          targets:
            - expr: "sum(rate(llm_quality_score_sum[1h])) by (model, criterion) / sum(rate(llm_quality_score_count[1h])) by (model, criterion)"
        - title: "Hallucination Rate"
          type: "gauge"
          targets:
            - expr: "sum(increase(llm_hallucination_detected_total[24h])) / sum(increase(llm_requests_total[24h]))"
    
    - title: "Error Rates"
      panels:
        - title: "Error Rate by Type"
          type: "graph"
          targets:
            - expr: "sum(rate(llm_error_total[5m])) by (error_type) / sum(rate(llm_requests_total[5m]))"
              legendFormat: "{{error_type}}"
        - title: "Error Rate by Provider"
          type: "graph"
          targets:
            - expr: "sum(rate(llm_error_total[5m])) by (provider) / sum(rate(llm_requests_total[5m])) by (provider)"
              legendFormat: "{{provider}}"
```

## Provider Reliability Monitoring

The system tracks the reliability of different LLM providers:

```python
class ProviderHealthMonitor:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.window_seconds = 300  # 5 minute window
        
        # Define metrics
        self.availability = Gauge(
            'llm_provider_availability',
            'LLM Provider Availability Percentage',
            ['provider']
        )
        self.latency = Gauge(
            'llm_provider_latency_p95',
            'LLM Provider P95 Latency',
            ['provider']
        )
        self.error_rate = Gauge(
            'llm_provider_error_rate',
            'LLM Provider Error Rate',
            ['provider', 'error_type']
        )
    
    def track_request(self, provider, success, latency=None, error_type=None):
        """Track a request to an LLM provider"""
        timestamp = int(time.time())
        
        # Add to time series in Redis
        request_key = f"llm:provider:{provider}:requests:{timestamp // 60}"
        self.redis.hincrby(request_key, "total", 1)
        if success:
            self.redis.hincrby(request_key, "success", 1)
        else:
            self.redis.hincrby(request_key, "error", 1)
            if error_type:
                self.redis.hincrby(request_key, f"error:{error_type}", 1)
        
        # Set expiry to keep only recent data
        self.redis.expire(request_key, self.window_seconds * 2)
        
        # Track latency if provided
        if latency is not None:
            latency_key = f"llm:provider:{provider}:latency:{timestamp // 60}"
            self.redis.lpush(latency_key, latency)
            self.redis.ltrim(latency_key, 0, 999)  # Keep last 1000 entries
            self.redis.expire(latency_key, self.window_seconds * 2)
    
    def update_metrics(self):
        """Update Prometheus metrics based on recent data"""
        now = int(time.time())
        window_start = now - self.window_seconds
        
        # Get all providers
        providers = set()
        for key in self.redis.scan_iter(match="llm:provider:*:requests:*"):
            provider = key.split(":")[2]
            providers.add(provider)
        
        # Calculate metrics for each provider
        for provider in providers:
            total_requests = 0
            success_requests = 0
            error_types = defaultdict(int)
            latencies = []
            
            # Collect request data
            for minute in range(window_start // 60, (now // 60) + 1):
                key = f"llm:provider:{provider}:requests:{minute}"
                if self.redis.exists(key):
                    data = self.redis.hgetall(key)
                    total_requests += int(data.get(b"total", 0))
                    success_requests += int(data.get(b"success", 0))
                    
                    # Collect error types
                    for field, value in data.items():
                        field_str = field.decode("utf-8")
                        if field_str.startswith("error:"):
                            error_type = field_str[6:]  # Remove "error:" prefix
                            error_types[error_type] += int(value)
            
            # Collect latency data
            for minute in range(window_start // 60, (now // 60) + 1):
                key = f"llm:provider:{provider}:latency:{minute}"
                if self.redis.exists(key):
                    values = self.redis.lrange(key, 0, -1)
                    latencies.extend([float(v) for v in values])
            
            # Calculate availability
            if total_requests > 0:
                availability = (success_requests / total_requests) * 100
                self.availability.labels(provider=provider).set(availability)
                
                # Calculate error rates
                for error_type, count in error_types.items():
                    error_rate = count / total_requests
                    self.error_rate.labels(
                        provider=provider,
                        error_type=error_type
                    ).set(error_rate)
            
            # Calculate P95 latency
            if latencies:
                latencies.sort()
                p95_index = int(len(latencies) * 0.95)
                p95_latency = latencies[p95_index]
                self.latency.labels(provider=provider).set(p95_latency)
```

## Model Performance Comparison

The system tracks comparative performance of different models:

```python
class ModelPerformanceTracker:
    def __init__(self):
        # Define metrics for comparing models
        self.comparative_quality = Gauge(
            'llm_comparative_quality',
            'Comparative Quality Score Between Models',
            ['model_a', 'model_b', 'criterion']
        )
        
        self.win_rate = Gauge(
            'llm_win_rate',
            'Win Rate in A/B Tests',
            ['model_a', 'model_b']
        )
        
        self.cost_performance_ratio = Gauge(
            'llm_cost_performance_ratio',
            'Cost-Performance Ratio',
            ['model']
        )
    
    def track_comparison(self, model_a, model_b, prompts, responses_a, responses_b, evaluations):
        """
        Track comparison between two models
        
        Args:
            model_a: First model
            model_b: Second model
            prompts: List of prompts used for comparison
            responses_a: Responses from model A
            responses_b: Responses from model B
            evaluations: Evaluation results
        """
        if not prompts or len(prompts) != len(responses_a) or len(prompts) != len(responses_b):
            return
        
        total_comparisons = len(prompts)
        wins_a = 0
        wins_b = 0
        
        for i in range(total_comparisons):
            eval_a = evaluations[i]['model_a']
            eval_b = evaluations[i]['model_b']
            
            # Track average scores by criterion
            for criterion in eval_a:
                if criterion in eval_b:
                    self.comparative_quality.labels(
                        model_a=model_a,
                        model_b=model_b,
                        criterion=criterion
                    ).set(eval_a[criterion] / eval_b[criterion])
            
            # Track win rate
            overall_a = sum(eval_a.values()) / len(eval_a)
            overall_b = sum(eval_b.values()) / len(eval_b)
            
            if overall_a > overall_b:
                wins_a += 1
            elif overall_b > overall_a:
                wins_b += 1
        
        # Update win rates
        if total_comparisons > 0:
            self.win_rate.labels(
                model_a=model_a,
                model_b=model_b
            ).set(wins_a / total_comparisons)
            
            self.win_rate.labels(
                model_a=model_b,
                model_b=model_a
            ).set(wins_b / total_comparisons)
    
    def update_cost_performance(self, metrics_by_model):
        """
        Update cost-performance ratio for each model
        
        Args:
            metrics_by_model: Dict with model metrics
        """
        for model, metrics in metrics_by_model.items():
            if 'quality' in metrics and 'cost' in metrics and metrics['cost'] > 0:
                ratio = metrics['quality'] / metrics['cost']
                self.cost_performance_ratio.labels(model=model).set(ratio)
```

## Context Window Utilization

The system monitors context window utilization for efficient token usage:

```python
def track_context_window_utilization(provider, model, input_tokens, max_context_length):
    """
    Track utilization of the context window
    
    Args:
        provider: LLM provider
        model: Model name
        input_tokens: Number of input tokens
        max_context_length: Maximum context length for the model
    """
    # Calculate utilization percentage
    utilization = (input_tokens / max_context_length) * 100
    
    # Track metric
    CONTEXT_UTILIZATION.labels(
        provider=provider,
        model=model
    ).observe(utilization)
    
    # Track distributions for analysis
    if utilization < 25:
        CONTEXT_UTILIZATION_BUCKET.labels(
            provider=provider,
            model=model,
            bucket="0-25"
        ).inc()
    elif utilization < 50:
        CONTEXT_UTILIZATION_BUCKET.labels(
            provider=provider,
            model=model,
            bucket="25-50"
        ).inc()
    elif utilization < 75:
        CONTEXT_UTILIZATION_BUCKET.labels(
            provider=provider,
            model=model,
            bucket="50-75"
        ).inc()
    elif utilization < 90:
        CONTEXT_UTILIZATION_BUCKET.labels(
            provider=provider,
            model=model,
            bucket="75-90"
        ).inc()
    else:
        CONTEXT_UTILIZATION_BUCKET.labels(
            provider=provider,
            model=model,
            bucket="90-100"
        ).inc()
    
    # Track near-limit requests (potential truncation risk)
    if utilization > 90:
        NEAR_CONTEXT_LIMIT.labels(
            provider=provider,
            model=model
        ).inc()
```

## Model Version Tracking

The system keeps track of model versions and their changes:

```python
class ModelVersionTracker:
    def __init__(self, db_client):
        self.db = db_client
        
        # Define metrics
        self.version_changes = Counter(
            'llm_model_version_changes_total',
            'LLM Model Version Changes',
            ['provider', 'model', 'from_version', 'to_version']
        )
    
    def track_model_version(self, provider, model, version):
        """Track model version and detect changes"""
        # Get current version from database
        current = self.db.get_model_version(provider, model)
        
        if current and current != version:
            # Version change detected
            self.version_changes.labels(
                provider=provider,
                model=model,
                from_version=current,
                to_version=version
            ).inc()
            
            # Store new version
            self.db.update_model_version(provider, model, version)
            
            # Log the change
            logger.info(
                "Model version change detected",
                provider=provider,
                model=model,
                from_version=current,
                to_version=version
            )
            
            # Trigger model evaluation
            asyncio.create_task(self.evaluate_model_change(provider, model, current, version))
        elif not current:
            # First time seeing this model
            self.db.update_model_version(provider, model, version)
    
    async def evaluate_model_change(self, provider, model, old_version, new_version):
        """Evaluate impact of model version change"""
        # Run benchmark tests on new model version
        test_results = await run_model_benchmarks(provider, model)
        
        # Store benchmark results
        self.db.store_benchmark_results(
            provider=provider,
            model=model,
            version=new_version,
            results=test_results
        )
        
        # Compare with previous benchmark results
        previous_results = self.db.get_benchmark_results(
            provider=provider,
            model=model,
            version=old_version
        )
        
        if previous_results:
            # Calculate performance differences
            for metric, value in test_results.items():
                if metric in previous_results:
                    change = ((value - previous_results[metric]) / previous_results[metric]) * 100
                    
                    # Track significant changes
                    if abs(change) > 5:  # 5% threshold
                        logger.info(
                            "Significant model performance change",
                            provider=provider,
                            model=model,
                            metric=metric,
                            old_value=previous_results[metric],
                            new_value=value,
                            change_percent=change
                        )
```

## LLM Failover Monitoring

The system tracks model failover events and their impact:

```python
class FailoverMonitor:
    def __init__(self):
        # Define metrics
        self.failover_events = Counter(
            'llm_failover_events_total',
            'LLM Failover Events',
            ['from_provider', 'from_model', 'to_provider', 'to_model', 'reason']
        )
        
        self.failover_latency = Histogram(
            'llm_failover_latency_seconds',
            'LLM Failover Latency in Seconds',
            ['from_provider', 'to_provider']
        )
        
        self.failed_requests = Counter(
            'llm_failed_requests_total',
            'Failed LLM Requests Count',
            ['provider', 'model', 'error_type']
        )
    
    def track_failover(self, from_provider, from_model, to_provider, to_model, reason, latency):
        """Track a failover event"""
        # Increment failover counter
        self.failover_events.labels(
            from_provider=from_provider,
            from_model=from_model,
            to_provider=to_provider,
            to_model=to_model,
            reason=reason
        ).inc()
        
        # Track failover latency
        self.failover_latency.labels(
            from_provider=from_provider,
            to_provider=to_provider
        ).observe(latency)
        
        # Log the event
        logger.info(
            "LLM failover occurred",
            from_provider=from_provider,
            from_model=from_model,
            to_provider=to_provider,
            to_model=to_model,
            reason=reason,
            latency=latency
        )
    
    def track_failure(self, provider, model, error_type):
        """Track a failed request"""
        self.failed_requests.labels(
            provider=provider,
            model=model,
            error_type=error_type
        ).inc()
```

## Conclusion

LLM-specific monitoring extends the general monitoring strategy with specialized metrics and tools for tracking the performance, quality, and reliability of LLM services. By implementing comprehensive LLM monitoring, the ColonyCraft AI platform can ensure high-quality AI responses, optimize costs, and maintain reliable service even when individual providers experience issues.
