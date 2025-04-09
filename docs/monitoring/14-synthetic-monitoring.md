# Synthetic Monitoring

## Automated Testing

Continuous synthetic transactions verify system health from the user perspective:

1. **API Health Checks**: Periodic calls to critical API endpoints
2. **Simulated User Journeys**: Automated tests of key user flows
3. **Cross-Region Verification**: Testing from multiple geographic locations

Example configuration:

```yaml
# Synthetic monitoring config
monitors:
  - name: "Basic Colony Creation"
    type: "api"
    url: "https://api.colonycraft.ai/v1/colonies"
    method: "POST"
    headers:
      Content-Type: "application/json"
      Authorization: "Bearer {{.SyntheticUserToken}}"
    body: |
      {
        "name": "Synthetic Test Colony",
        "template": "basic",
        "resources": {
          "compute": "standard",
          "storage": 5
        }
      }
    assertions:
      - type: "status"
        value: 201
      - type: "responseTime"
        value: 1000
    frequency: "5m"
    locations:
      - "us-east"
      - "eu-west"
      - "ap-southeast"
```

## Browser Simulation

For UI-focused monitoring, headless browser testing is implemented:

1. **End-to-End Flows**: Automated browser sessions test complete user journeys
2. **Screenshot Comparisons**: Visual regression testing for UI components
3. **Performance Metrics**: Tracking page load times, time-to-interactive, etc.

Example Playwright script for synthetic testing:

```javascript
// ui-monitor.js
const { chromium } = require('playwright');
const metrics = require('./metrics-client');

async function monitorLoginFlow() {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  // Start timing
  const startTime = Date.now();
  
  try {
    // Navigate to login page
    await page.goto('https://app.colonycraft.ai/login');
    
    // Track navigation time
    metrics.recordTiming('login_page_load', Date.now() - startTime);
    
    // Fill in login form
    await page.fill('input[name="email"]', process.env.SYNTHETIC_USER_EMAIL);
    await page.fill('input[name="password"]', process.env.SYNTHETIC_USER_PASSWORD);
    
    // Click login button
    const responsePromise = page.waitForResponse(response => 
      response.url().includes('/api/v1/auth/login') && response.status() === 200
    );
    await page.click('button[type="submit"]');
    await responsePromise;
    
    // Track total login time
    metrics.recordTiming('login_flow_complete', Date.now() - startTime);
    
    // Verify successful login
    await page.waitForSelector('.dashboard-welcome', { timeout: 5000 });
    
    // Record success
    metrics.incrementCounter('login_flow_success');
  } catch (error) {
    // Record failure
    metrics.incrementCounter('login_flow_failure');
    console.error(`Login flow failed: ${error.message}`);
    
    // Take screenshot of failure
    await page.screenshot({ path: `failure-${Date.now()}.png` });
    
    throw error;
  } finally {
    await browser.close();
  }
}

// Execute monitoring
monitorLoginFlow().catch(console.error);
```

## Key User Journeys

The synthetic monitoring system tests the following key user journeys:

1. **User Registration and Login**: Testing account creation and authentication
2. **Colony Creation**: Creating new colonies with different templates
3. **Agent Deployment**: Deploying AI agents within colonies
4. **Resource Management**: Managing compute and storage resources
5. **Collaboration**: Testing collaboration features between users

Each journey is broken down into individual steps with specific validations at each point:

```javascript
// Example of a complete journey test
async function testEndToEndJourney() {
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();
  
  const metrics = {
    timings: {},
    successes: 0,
    failures: 0,
    screenshots: []
  };
  
  try {
    // Step 1: Registration
    metrics.timings.registrationStart = Date.now();
    await page.goto('https://app.colonycraft.ai/register');
    
    // Generate unique test user
    const testUser = `test-user-${Date.now()}@synthetic.colonycraft.ai`;
    const testPassword = `Test${Date.now()}!`;
    
    await page.fill('input[name="email"]', testUser);
    await page.fill('input[name="password"]', testPassword);
    await page.fill('input[name="confirmPassword"]', testPassword);
    
    await page.click('button[type="submit"]');
    await page.waitForSelector('.welcome-screen');
    metrics.timings.registrationComplete = Date.now();
    metrics.successes++;
    
    // Step 2: Create Colony
    metrics.timings.colonyCreationStart = Date.now();
    await page.click('a[href="/colonies/create"]');
    
    await page.fill('input[name="colonyName"]', `Synthetic Test Colony ${Date.now()}`);
    await page.selectOption('select[name="template"]', 'data-analysis');
    
    await page.click('button.create-colony-button');
    await page.waitForSelector('.colony-dashboard');
    metrics.timings.colonyCreationComplete = Date.now();
    metrics.successes++;
    
    // Take screenshot of colony dashboard
    const colonyScreenshot = await page.screenshot();
    metrics.screenshots.push({
      name: 'colony-dashboard',
      data: colonyScreenshot,
      timestamp: Date.now()
    });
    
    // Step 3: Deploy Agent
    metrics.timings.agentDeploymentStart = Date.now();
    await page.click('button.add-agent');
    
    await page.fill('input[name="agentName"]', `Test Agent ${Date.now()}`);
    await page.selectOption('select[name="agentType"]', 'data-processor');
    
    await page.click('button.deploy-agent-button');
    await page.waitForSelector('.agent-status.running');
    metrics.timings.agentDeploymentComplete = Date.now();
    metrics.successes++;
    
    // Step 4: Run Agent Task
    metrics.timings.agentTaskStart = Date.now();
    await page.click('.agent-card');
    await page.click('button.run-task');
    
    await page.fill('textarea[name="prompt"]', 'Process the sample data and generate a summary');
    await page.click('button.submit-task');
    
    // Wait for task to complete
    await page.waitForSelector('.task-result', { timeout: 30000 });
    metrics.timings.agentTaskComplete = Date.now();
    metrics.successes++;
    
    // Take screenshot of task result
    const taskScreenshot = await page.screenshot();
    metrics.screenshots.push({
      name: 'task-result',
      data: taskScreenshot,
      timestamp: Date.now()
    });
    
    // Step 5: Logout
    await page.click('.user-menu');
    await page.click('a.logout');
    await page.waitForSelector('.login-form');
    metrics.successes++;
    
    // Report successful journey
    console.log(`End-to-end journey completed successfully: ${metrics.successes} steps passed`);
    
    // Calculate timing metrics
    const timingMetrics = {
      registration: metrics.timings.registrationComplete - metrics.timings.registrationStart,
      colonyCreation: metrics.timings.colonyCreationComplete - metrics.timings.colonyCreationStart,
      agentDeployment: metrics.timings.agentDeploymentComplete - metrics.timings.agentDeploymentStart,
      agentTask: metrics.timings.agentTaskComplete - metrics.timings.agentTaskStart,
      total: Date.now() - metrics.timings.registrationStart
    };
    
    // Report timing metrics to monitoring system
    Object.entries(timingMetrics).forEach(([metric, value]) => {
      console.log(`${metric}: ${value}ms`);
      metrics.recordTiming(`e2e_${metric}`, value);
    });
    
    // Report success to monitoring system
    metrics.incrementCounter('e2e_journey_success');
    
    // Upload screenshots for visual regression testing
    await uploadScreenshotsForComparison(metrics.screenshots);
    
  } catch (error) {
    // Report failure
    metrics.failures++;
    metrics.incrementCounter('e2e_journey_failure');
    console.error(`End-to-end journey failed at step ${metrics.successes + 1}: ${error.message}`);
    
    // Take screenshot of failure
    const failureScreenshot = await page.screenshot();
    await saveFailureEvidence({
      screenshot: failureScreenshot,
      error: error.message,
      step: metrics.successes + 1,
      url: page.url(),
      timestamp: Date.now()
    });
  } finally {
    await browser.close();
  }
}
```

## Global Testing Network

Synthetic tests are executed from multiple geographic locations to verify system performance across regions:

1. **Global Regions**: Tests run from North America, Europe, Asia, and Australia
2. **Network Variability**: Tests with different network conditions (latency, bandwidth)
3. **Browser Coverage**: Tests across Chrome, Firefox, Safari, and Edge
4. **Device Simulation**: Mobile and desktop device simulation

The testing infrastructure is hosted on cloud providers in each region:

```
┌───────────────────┐     ┌───────────────────┐     ┌───────────────────┐
│  North America    │     │       Europe      │     │        Asia       │
│                   │     │                   │     │                   │
│  - US East        │     │  - EU West        │     │  - Asia East      │
│  - US West        │     │  - EU Central     │     │  - Asia Southeast │
│  - US Central     │     │  - EU North       │     │  - India          │
└─────────┬─────────┘     └─────────┬─────────┘     └─────────┬─────────┘
          │                         │                         │
          │                         │                         │
          ▼                         ▼                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       Central Monitoring Service                         │
│                                                                         │
│  - Aggregates test results                                              │
│  - Compares regional performance                                        │
│  - Alerts on regional issues                                            │
│  - Stores historical data                                               │
└─────────────────────────────────────────────────────────────────────────┘
```

## Visual Regression Testing

The synthetic monitoring system includes visual regression testing to detect UI changes:

1. **Baseline Images**: Approved screenshots of key UI components
2. **Pixel Comparison**: Comparison of new screenshots against baselines
3. **Highlighting Changes**: Visual indication of detected differences
4. **Approval Workflow**: Process for reviewing and approving changes

Example visual regression implementation:

```javascript
const { PNG } = require('pngjs');
const pixelmatch = require('pixelmatch');
const fs = require('fs');

async function compareScreenshots(baseline, current) {
  // Read images
  const img1 = PNG.sync.read(fs.readFileSync(baseline));
  const img2 = PNG.sync.read(fs.readFileSync(current));
  
  // Create output image
  const { width, height } = img1;
  const diff = new PNG({ width, height });
  
  // Compare images
  const numDiffPixels = pixelmatch(
    img1.data,
    img2.data,
    diff.data,
    width,
    height,
    { threshold: 0.1 }
  );
  
  // Calculate percentage difference
  const diffPercentage = (numDiffPixels / (width * height)) * 100;
  
  // Save diff image
  fs.writeFileSync('diff.png', PNG.sync.write(diff));
  
  return {
    diffPixels: numDiffPixels,
    diffPercentage,
    diffImage: 'diff.png',
    hasDifference: diffPercentage > 0.1 // More than 0.1% different
  };
}

async function processVisualRegression(testName, screenshotPath) {
  const baselinePath = `./baselines/${testName}.png`;
  
  // Check if baseline exists
  if (!fs.existsSync(baselinePath)) {
    console.log(`No baseline found for ${testName}, creating one`);
    fs.copyFileSync(screenshotPath, baselinePath);
    return {
      status: 'baseline_created',
      message: 'Initial baseline created'
    };
  }
  
  // Compare with baseline
  const result = await compareScreenshots(baselinePath, screenshotPath);
  
  if (result.hasDifference) {
    console.log(`Visual changes detected in ${testName}: ${result.diffPercentage.toFixed(2)}% different`);
    
    // Save current screenshot for review
    const reviewPath = `./review/${testName}_${Date.now()}.png`;
    fs.copyFileSync(screenshotPath, reviewPath);
    
    // Save diff image
    const diffPath = `./review/${testName}_${Date.now()}_diff.png`;
    fs.copyFileSync(result.diffImage, diffPath);
    
    return {
      status: 'changes_detected',
      diffPercentage: result.diffPercentage,
      reviewPath,
      diffPath
    };
  }
  
  return {
    status: 'no_changes',
    message: 'No visual changes detected'
  };
}
```

## Performance Testing

The synthetic monitoring system includes performance testing:

1. **Page Load Performance**: Tracking key loading metrics
2. **API Response Times**: Measuring API endpoint performance
3. **Resource Utilization**: Monitoring resource usage during testing
4. **Throughput Testing**: Measuring system capacity

Example performance measurement:

```javascript
async function measurePagePerformance(url) {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  // Enable performance metrics collection
  await page.setRequestInterception(true);
  
  const requests = [];
  const responses = [];
  let domContentLoaded = 0;
  let loaded = 0;
  
  page.on('request', request => {
    requests.push({
      url: request.url(),
      method: request.method(),
      resourceType: request.resourceType(),
      timestamp: Date.now()
    });
    request.continue();
  });
  
  page.on('response', response => {
    responses.push({
      url: response.url(),
      status: response.status(),
      contentType: response.headers()['content-type'],
      timestamp: Date.now()
    });
  });
  
  page.on('domcontentloaded', () => {
    domContentLoaded = Date.now();
  });
  
  page.on('load', () => {
    loaded = Date.now();
  });
  
  const startTime = Date.now();
  
  try {
    // Navigate to the page
    await page.goto(url, { waitUntil: 'networkidle' });
    
    // Collect performance metrics
    const performanceMetrics = await page.evaluate(() => {
      return {
        // Navigation Timing API metrics
        navigationTiming: performance.getEntriesByType('navigation')[0],
        // Resource Timing API metrics
        resourceTiming: performance.getEntriesByType('resource'),
        // First Paint and First Contentful Paint
        paintTiming: performance.getEntriesByType('paint'),
        // Largest Contentful Paint
        lcpTiming: performance.getEntriesByName('largest-contentful-paint'),
        // First Input Delay
        fidTiming: performance.getEntriesByName('first-input-delay')
      };
    });
    
    // Record timing metrics
    const timings = {
      ttfb: performanceMetrics.navigationTiming.responseStart - performanceMetrics.navigationTiming.requestStart,
      fcp: performanceMetrics.paintTiming.find(entry => entry.name === 'first-contentful-paint')?.startTime,
      lcp: performanceMetrics.lcpTiming[0]?.startTime,
      domContentLoaded: domContentLoaded - startTime,
      loadComplete: loaded - startTime,
      totalRequests: requests.length,
      totalSize: performanceMetrics.resourceTiming.reduce((total, resource) => total + (resource.transferSize || 0), 0)
    };
    
    // Calculate Core Web Vitals
    const coreWebVitals = {
      lcp: timings.lcp, // Largest Contentful Paint
      fid: performanceMetrics.fidTiming[0]?.duration, // First Input Delay
      cls: await page.evaluate(() => window.cumulativeLayoutShift) // Cumulative Layout Shift
    };
    
    // Report metrics to monitoring system
    Object.entries(timings).forEach(([metric, value]) => {
      metrics.recordTiming(`page_${metric}`, value);
    });
    
    // Report Core Web Vitals
    Object.entries(coreWebVitals).forEach(([metric, value]) => {
      if (value !== undefined) {
        metrics.recordTiming(`core_web_vitals_${metric}`, value);
      }
    });
    
    return {
      url,
      timings,
      coreWebVitals,
      requestCount: requests.length,
      resourceCount: performanceMetrics.resourceTiming.length
    };
  } finally {
    await browser.close();
  }
}
```

## Synthetic User Profiles

The synthetic monitoring system uses different user profiles to test various usage patterns:

1. **New User**: Testing the onboarding experience
2. **Power User**: Testing advanced features with high usage
3. **Enterprise User**: Testing collaboration and organization features
4. **Mobile User**: Testing from mobile devices
5. **International User**: Testing from different regions with different languages

Example user profile configuration:

```yaml
# Synthetic user profiles
users:
  - id: "new-user"
    type: "new"
    properties:
      skipTutorial: false
      exploreFeatures: true
      performBasicActions: true
      testPath: "onboarding"
  
  - id: "power-user"
    type: "power"
    properties:
      colonyCount: 10
      agentsPerColony: 5
      complexWorkflows: true
      advancedFeatures: true
      testPath: "power-usage"
  
  - id: "enterprise-user"
    type: "enterprise"
    properties:
      organizationSize: "large"
      teamMembers: 25
      sharedResources: true
      permissionTests: true
      testPath: "enterprise"
  
  - id: "mobile-user"
    type: "mobile"
    properties:
      deviceType: "mobile"
      screenSize: "small"
      networkCondition: "variable"
      testPath: "mobile"
  
  - id: "international-user"
    type: "international"
    properties:
      region: "europe"
      language: "fr-FR"
      timezone: "Europe/Paris"
      testPath: "international"
```

## Chaos Testing

The synthetic monitoring system includes chaos testing to verify system resilience:

1. **Service Disruption**: Simulating service outages
2. **Network Issues**: Introducing network latency and packet loss
3. **Resource Constraints**: Limiting CPU and memory resources
4. **Dependency Failures**: Simulating third-party service failures

Example chaos testing implementation:

```javascript
async function performChaosTest(target, chaosType, duration) {
  console.log(`Starting chaos test: ${chaosType} on ${target} for ${duration}s`);
  
  // Start chaos action
  const chaosId = await startChaosAction(target, chaosType, duration);
  
  // Run synthetic tests during chaos
  const testResults = [];
  const startTime = Date.now();
  const endTime = startTime + (duration * 1000);
  
  while (Date.now() < endTime) {
    // Run key synthetic tests
    const result = await runSyntheticTest('critical-path');
    testResults.push(result);
    
    // Wait before next test
    await new Promise(resolve => setTimeout(resolve, 10000));
  }
  
  // Stop chaos action
  await stopChaosAction(chaosId);
  
  // Analyze results
  const successRate = testResults.filter(r => r.success).length / testResults.length;
  const avgResponseTime = testResults.reduce((sum, r) => sum + r.responseTime, 0) / testResults.length;
  
  console.log(`Chaos test completed: ${successRate * 100}% success rate, ${avgResponseTime}ms avg response time`);
  
  // Report results to monitoring system
  metrics.recordGauge(`chaos_test_success_rate`, successRate * 100);
  metrics.recordTiming(`chaos_test_response_time`, avgResponseTime);
  
  return {
    chaosType,
    target,
    duration,
    testCount: testResults.length,
    successRate,
    averageResponseTime: avgResponseTime,
    results: testResults
  };
}

// Example chaos actions
async function startChaosAction(target, chaosType, duration) {
  // Call chaos orchestration API
  const response = await fetch('https://chaos.colonycraft.ai/api/actions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      target,
      type: chaosType,
      duration
    })
  });
  
  const data = await response.json();
  return data.id;
}

async function stopChaosAction(chaosId) {
  // Call chaos orchestration API to stop action
  await fetch(`https://chaos.colonycraft.ai/api/actions/${chaosId}`, {
    method: 'DELETE'
  });
}
```

## Integration with Monitoring System

Synthetic monitoring results are integrated with the central monitoring system:

1. **Unified Dashboards**: Synthetic test results displayed alongside real user metrics
2. **Correlated Alerts**: Alerts correlated with synthetic test failures
3. **Historical Trends**: Historical data for performance comparison
4. **Geographic Comparison**: Comparison of performance across regions

Example of the integration:

```javascript
// Exporting synthetic test results to Prometheus
class PrometheusExporter {
  constructor(gatewayUrl) {
    this.gatewayUrl = gatewayUrl;
    
    // Define metrics
    this.metrics = {
      testSuccess: 'synthetic_test_success',
      testDuration: 'synthetic_test_duration_seconds',
      stepSuccess: 'synthetic_step_success',
      stepDuration: 'synthetic_step_duration_seconds',
      resourceSize: 'synthetic_resource_size_bytes',
      resourceCount: 'synthetic_resource_count',
      responseTime: 'synthetic_response_time_seconds'
    };
  }
  
  async exportTestResult(result) {
    const metrics = [];
    
    // Add test success metric
    metrics.push({
      name: this.metrics.testSuccess,
      value: result.success ? 1 : 0,
      labels: {
        test: result.name,
        location: result.location,
        browser: result.browser
      }
    });
    
    // Add test duration metric
    metrics.push({
      name: this.metrics.testDuration,
      value: result.duration / 1000, // Convert to seconds
      labels: {
        test: result.name,
        location: result.location,
        browser: result.browser
      }
    });
    
    // Add step metrics
    for (const step of result.steps) {
      metrics.push({
        name: this.metrics.stepSuccess,
        value: step.success ? 1 : 0,
        labels: {
          test: result.name,
          step: step.name,
          location: result.location,
          browser: result.browser
        }
      });
      
      metrics.push({
        name: this.metrics.stepDuration,
        value: step.duration / 1000, // Convert to seconds
        labels: {
          test: result.name,
          step: step.name,
          location: result.location,
          browser: result.browser
        }
      });
    }
    
    // Add resource metrics
    metrics.push({
      name: this.metrics.resourceCount,
      value: result.resources.length,
      labels: {
        test: result.name,
        location: result.location,
        browser: result.browser
      }
    });
    
    // Add response time metrics for API calls
    for (const request of result.requests) {
      if (request.type === 'xhr' || request.type === 'fetch') {
        metrics.push({
          name: this.metrics.responseTime,
          value: request.duration / 1000, // Convert to seconds
          labels: {
            test: result.name,
            url: request.url.replace(/\/[0-9]+/g, '/:id'), // Normalize URLs
            method: request.method,
            status: request.status,
            location: result.location,
            browser: result.browser
          }
        });
      }
    }
    
    // Push metrics to Prometheus Pushgateway
    await this.pushMetrics(metrics);
  }
  
  async pushMetrics(metrics) {
    const payload = metrics.map(metric => {
      const labels = Object.entries(metric.labels)
        .map(([key, value]) => `${key}="${value}"`)
        .join(',');
      
      return `${metric.name}{${labels}} ${metric.value}`;
    }).join('\n');
    
    await fetch(this.gatewayUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain' },
      body: payload
    });
  }
}
```

## Conclusion

Synthetic monitoring provides proactive validation of system functionality and performance from the user perspective. By continuously testing key user journeys across different regions and browsers, potential issues can be detected and resolved before they impact real users.

The combination of API health checks, browser simulation, visual regression testing, and performance measurement provides comprehensive coverage of the ColonyCraft AI platform, ensuring a reliable and performant user experience.
