# app.py
from flask import Flask, jsonify, request
from agent import AIAgent
import redis
import json
import uuid
from threading import Thread
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
agent = AIAgent()

# Initialize Redis for task storage
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    decode_responses=True
)

def execute_task_async(task_id: str, task_description: str):
    """Execute task asynchronously and store results in Redis."""
    try:
        # Update task status to running
        redis_client.hset(f"task:{task_id}", "status", "running")
        
        # Execute task
        results = agent.execute_task(task_description)
        
        # Store results
        redis_client.hset(
            f"task:{task_id}",
            mapping={
                "status": "completed",
                "results": json.dumps(results),
                "error": ""
            }
        )
    except Exception as e:
        # Store error if task fails
        redis_client.hset(
            f"task:{task_id}",
            mapping={
                "status": "failed",
                "error": str(e)
            }
        )

@app.route('/tasks', methods=['POST'])
def create_task():
    """Create a new task."""
    data = request.get_json()
    
    if not data or 'task' not in data:
        return jsonify({"error": "No task provided"}), 400
    
    task_id = str(uuid.uuid4())
    
    # Initialize task in Redis
    redis_client.hset(
        f"task:{task_id}",
        mapping={
            "task": data['task'],
            "status": "pending",
            "results": "",
            "error": ""
        }
    )
    redis_client.expire(f"task:{task_id}", 3600)  # Expire after 1 hour
    
    # Start task execution in background
    Thread(target=execute_task_async, args=(task_id, data['task'])).start()
    
    return jsonify({
        "task_id": task_id,
        "status": "pending",
        "message": "Task created successfully"
    })

@app.route('/tasks/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """Get task status and results."""
    task_data = redis_client.hgetall(f"task:{task_id}")
    
    if not task_data:
        return jsonify({"error": "Task not found"}), 404
    
    response = {
        "task_id": task_id,
        "task": task_data.get("task", ""),
        "status": task_data.get("status", "unknown")
    }
    
    # Include results if task is completed
    if task_data.get("status") == "completed":
        response["results"] = json.loads(task_data.get("results", "[]"))
    
    # Include error if task failed
    if task_data.get("status") == "failed":
        response["error"] = task_data.get("error", "Unknown error")
    
    return jsonify(response)

@app.route('/tasks', methods=['GET'])
def list_tasks():
    """List all active tasks."""
    tasks = []
    for key in redis_client.scan_iter("task:*"):
        task_data = redis_client.hgetall(key)
        task_id = key.split(":")[-1]
        tasks.append({
            "task_id": task_id,
            "task": task_data.get("task", ""),
            "status": task_data.get("status", "unknown")
        })
    return jsonify({"tasks": tasks})

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy"})

if __name__ == "__main__":
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
