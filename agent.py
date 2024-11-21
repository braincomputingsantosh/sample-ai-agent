# agent.py
import os
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from openai import OpenAI
from tavily import TavilyClient
from dotenv import load_dotenv
import json
import time

# Load environment variables
load_dotenv()

class Tool(BaseModel):
    name: str
    description: str
    function: Any

class AgentState(BaseModel):
    current_task: str = ""
    memory: List[Dict] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)

class AIAgent:
    def __init__(self):
        # Initialize clients
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.tavily_client = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))
        
        # Initialize state
        self.state = AgentState()
        
        # Initialize tools
        self.tools = self._initialize_tools()

    def _initialize_tools(self) -> List[Tool]:
        """Initialize available tools for the agent."""
        return [
            Tool(
                name="web_search",
                description="Search the web for information",
                function=self._search_web
            ),
            Tool(
                name="analyze_text",
                description="Analyze text using OpenAI",
                function=self._analyze_text
            ),
            Tool(
                name="summarize",
                description="Summarize given text",
                function=self._summarize_text
            )
        ]

    def _search_web(self, query: str) -> Dict:
        """Perform a web search using Tavily."""
        try:
            results = self.tavily_client.search(query=query, search_depth="basic")
            return {"status": "success", "results": results}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _analyze_text(self, text: str) -> Dict:
        """Analyze text using OpenAI."""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Analyze the following text and provide insights:"},
                    {"role": "user", "content": text}
                ]
            )
            return {"status": "success", "analysis": response.choices[0].message.content}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _summarize_text(self, text: str) -> Dict:
        """Summarize text using OpenAI."""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Provide a concise summary of the following text:"},
                    {"role": "user", "content": text}
                ]
            )
            return {"status": "success", "summary": response.choices[0].message.content}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _decide_next_action(self, task: str) -> Dict:
        """Decide the next action based on the current task."""
        try:
            prompt = f"""
            Current task: {task}
            Available tools: {[tool.name for tool in self.tools]}
            
            Decide the next best action to take. Return your response as JSON with these fields:
            - tool_name: which tool to use
            - input: what input to provide to the tool
            - reasoning: why this action was chosen
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a decision-making AI. Respond in JSON format."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def update_memory(self, action: Dict, result: Dict):
        """Update agent's memory with action and result."""
        self.state.memory.append({
            "timestamp": time.time(),
            "action": action,
            "result": result
        })

    def execute_task(self, task: str) -> List[Dict]:
        """Execute a given task using available tools."""
        self.state.current_task = task
        results = []
        
        # Maximum steps to prevent infinite loops
        max_steps = 5
        current_step = 0
        
        while current_step < max_steps:
            # Decide next action
            action = self._decide_next_action(task)
            
            if action.get("status") == "error":
                results.append({"error": "Failed to decide next action"})
                break
                
            # Find the appropriate tool
            tool = next((t for t in self.tools if t.name == action["tool_name"]), None)
            if not tool:
                results.append({"error": f"Tool {action['tool_name']} not found"})
                break
            
            # Execute the action
            result = tool.function(action["input"])
            
            # Update memory
            self.update_memory(action, result)
            
            # Add to results
            results.append({
                "step": current_step + 1,
                "action": action,
                "result": result
            })
            
            # Check if task is complete
            if result.get("status") == "success":
                break
                
            current_step += 1
        
        return results

# Example usage
if __name__ == "__main__":
    agent = AIAgent()
    
    # Example task
    task = "Find and summarize the latest news about artificial intelligence"
    print(f"Executing task: {task}")
    
    results = agent.execute_task(task)
    
    print("\nTask Results:")
    for result in results:
        print(json.dumps(result, indent=2))
