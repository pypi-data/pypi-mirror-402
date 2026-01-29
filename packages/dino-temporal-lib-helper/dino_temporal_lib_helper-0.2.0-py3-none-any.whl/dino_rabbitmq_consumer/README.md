# RabbitMQ Consumer for AI Audio Match

## Overview

RabbitMQ Consumer mode allows the AI Audio Match system to consume messages from a RabbitMQ queue and automatically start Temporal workflows based on the messages. This enables asynchronous, queue-based processing with intelligent workflow capacity management.

## Features

- **Smart Workflow Management**: Automatically monitors running workflow count and fetches messages when capacity is available
- **Configurable Thresholds**: Set min/max concurrent workflow limits
- **Batch Processing**: Fetches multiple messages at once for efficiency
- **Automatic Retry**: Built-in retry mechanism with dead letter queue support
- **Health Monitoring**: Real-time statistics and health checks
- **Graceful Shutdown**: Handles shutdown signals properly

## Configuration

### Environment Variables

```bash
# RabbitMQ Connection
export RABBITMQ_HOST="localhost"
export RABBITMQ_PORT="5672"
export RABBITMQ_USERNAME="guest"
export RABBITMQ_PASSWORD="guest"
export RABBITMQ_VHOST="/"

# Queue Configuration
export RABBITMQ_QUEUE="ai-audio-match-queue"
export RABBITMQ_EXCHANGE="ai-audio-match-exchange"
export RABBITMQ_ROUTING_KEY="audio.process"
export RABBITMQ_PREFETCH="10"

# Workflow Management
export MAX_CONCURRENT_WORKFLOWS="50"
export WORKFLOW_CHECK_INTERVAL="30"

# Consumer Settings
export RETRY_ATTEMPTS="3"
export RETRY_DELAY="60"
export DEAD_LETTER_QUEUE="ai-audio-match-dlq"
export CONSUMER_TAG="ai-audio-match-consumer"
```

## Usage

### 1. Running RabbitMQ Consumer Mode

```bash
# Run only RabbitMQ consumer
python main.py --mode rabbitmq

# With custom configuration
export MAX_CONCURRENT_WORKFLOWS=100
python main.py --mode rabbitmq --log-level debug
```

### 2. Message Format

#### Query Message
```json
{
  "type": "query",
  "data": {
    "uri": "https://example.com/audio.mp3",
    "custom_id": "query-001",
    "top_k": 5,
    "threshold": 0.03,
    "continuous_delta": 2.0
  },
  "timestamp": "2025-08-29T00:00:00Z"
}
```

#### Index Message
```json
{
  "type": "index", 
  "data": {
    "uri": "https://example.com/audio.mp3",
    "custom_id": "index-001",
    "file_name": "audio.mp3"
  },
  "timestamp": "2025-08-29T00:00:00Z"
}
```

### 3. Testing with RabbitMQ Test Client

```bash
# Send a single query message
python rabbitmq_test_client.py query "https://example.com/test.mp3" "test-001"

# Send a single index message
python rabbitmq_test_client.py index "https://example.com/test.mp3" "test-001"

# Send batch of test messages
python rabbitmq_test_client.py batch 10

# Show configuration
python rabbitmq_test_client.py config
```

## How It Works

### 1. Workflow Capacity Management

The consumer continuously monitors the number of running Temporal workflows:

- **Max Threshold**: When running workflows >= `MAX_CONCURRENT_WORKFLOWS`, stop fetching new messages

### 2. Message Processing Flow

1. Consumer checks workflow capacity every `WORKFLOW_CHECK_INTERVAL` seconds
2. If capacity available, fetches batch of messages from RabbitMQ
3. For each message:
   - Validates message format
   - Checks if new workflow can be started
   - Creates appropriate InputQueryRequest/InputIndexRequest
   - Starts Temporal workflow
   - Acknowledges message on success

### 3. Error Handling

- **Invalid JSON**: Message rejected without requeue
- **Unknown message type**: Message rejected without requeue  
- **Workflow start failure**: Message rejected with requeue for retry
- **Capacity reached**: Message processing delayed until capacity available
- **Dead Letter Queue**: Failed messages after max retries go to DLQ

## Monitoring

### 1. API Endpoints (when API mode also running)

```bash
# Get comprehensive system stats including RabbitMQ consumer
curl http://localhost:6006/api/v1/admin/stats

# Get RabbitMQ consumer specific status
curl http://localhost:6006/api/v1/admin/rabbitmq-status
```

### 2. Log Monitoring

The consumer provides structured JSON logs for easy monitoring:

```json
{
  "timestamp": "2025-08-29T10:00:00Z",
  "level": "INFO",
  "logger": "rabbitmq_consumer.consumer",
  "message": "Workflow capacity status",
  "running_workflows": 15,
  "max_concurrent": 50,
  "should_fetch": false
}
```

## Deployment

### 1. Docker

```dockerfile
# Use the existing Dockerfile
FROM pytorch/pytorch:2.8.0-cuda12.9-cudnn9-runtime

# ... (existing dockerfile content)

# Run RabbitMQ consumer mode
CMD ["python", "main.py", "--mode", "rabbitmq"]
```

### 2. Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-audio-match-rabbitmq-consumer
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: consumer
        image: ai-audio-match:latest
        command: ["python", "main.py", "--mode", "rabbitmq"]
        env:
        - name: RABBITMQ_HOST
          value: "rabbitmq.default.svc.cluster.local"
        - name: MAX_CONCURRENT_WORKFLOWS
          value: "50"
        # ... other env vars
```

### 3. Docker Compose

```yaml
version: '3.8'
services:
  rabbitmq:
    image: rabbitmq:3-management
    ports:
      - "5672:5672"
      - "15672:15672"
    environment:
      RABBITMQ_DEFAULT_USER: admin
      RABBITMQ_DEFAULT_PASS: password

  temporal:
    image: temporalio/auto-setup:latest
    ports:
      - "7233:7233"

  ai-audio-match-consumer:
    build: .
    command: ["python", "main.py", "--mode", "rabbitmq"]
    depends_on:
      - rabbitmq
      - temporal
    environment:
      RABBITMQ_HOST: rabbitmq
      RABBITMQ_USERNAME: admin
      RABBITMQ_PASSWORD: password
      HOST_TEMPORAL: temporal:7233
      MAX_CONCURRENT_WORKFLOWS: 20
```

## Troubleshooting

### Common Issues

1. **Connection Failures**
   ```bash
   # Check RabbitMQ is running
   curl http://localhost:15672
   
   # Check Temporal is running  
   temporal workflow list
   ```

2. **No Messages Being Processed**
   - Check workflow capacity: running workflows might be at max
   - Verify queue has messages: use RabbitMQ management UI
   - Check consumer logs for errors

3. **High Memory Usage**
   - Reduce `MAX_CONCURRENT_WORKFLOWS`
   - Monitor workflow cleanup logs

### Debug Mode

```bash
# Run with debug logging
export LOG_LEVEL=DEBUG
python main.py --mode rabbitmq --log-level debug
```

## Best Practices

1. **Capacity Planning**: Set `MAX_CONCURRENT_WORKFLOWS` based on available resources
2. **Monitoring**: Use structured logs and API endpoints for monitoring
3. **Error Handling**: Monitor dead letter queue for failed messages
4. **Graceful Shutdown**: Always use proper signal handling in production
5. **Resource Limits**: Set appropriate Kubernetes resource limits
6. **Health Checks**: Use readiness/liveness probes in Kubernetes deployments
