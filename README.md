This web service version of the AI agent includes:

1. **API Endpoints:**
   - `POST /tasks`: Create new tasks
   - `GET /tasks/<task_id>`: Get task status and results
   - `GET /tasks`: List all active tasks
   - `GET /health`: Health check

2. **Features:**
   - Asynchronous task execution
   - Redis for task state management
   - Docker Compose setup with Redis
   - Task expiration (1 hour)
   - Error handling

To run the service:

1. Using Docker Compose (recommended):
```bash
docker-compose up --build
```

2. Using just Docker:
```bash
# Start Redis
docker run -d -p 6379:6379 redis:alpine

# Build and run the agent service
docker build -t ai-agent-service .
docker run -p 5000:5000 --env-file .env ai-agent-service
```

Example usage:

1. Create a new task:
```bash
curl -X POST http://localhost:5000/tasks \
  -H "Content-Type: application/json" \
  -d '{"task": "Research the latest developments in quantum computing"}'
```

2. Check task status:
```bash
curl http://localhost:5000/tasks/<task_id>
```

3. List all tasks:
```bash
curl http://localhost:5000/tasks
```

Example response for a completed task:
```json
{
  "task_id": "123e4567-e89b-12d3-a456-426614174000",
  "task": "Research quantum computing",
  "status": "completed",
  "results": [
    {
      "step": 1,
      "action": {
        "tool_name": "web_search",
        "input": "latest developments quantum computing",
        "reasoning": "Starting with web search to gather recent information"
      },
      "result": {
        "status": "success",
        "results": [...]
      }
    },
    ...
  ]
}
```
You can also run ```python agent.py``` the agent as a stand alone. Make sure to create and setup the .env file
```
agent = AIAgent()
results = agent.execute_task("Research the latest developments in quantum computing")
```
