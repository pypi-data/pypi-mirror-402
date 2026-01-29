# 🏭 Sasefied - Industry-Specific AI Agents

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Documentation](https://img.shields.io/badge/documentation-excellent-brightgreen.svg)](docs/)

> Comprehensive AI-powered agents specialized for different business sectors. Each module provides domain-specific expertise, intelligent routing, and collaborative problem-solving capabilities.

## ✨ Features

- 🎯 **Industry Expertise** - Deep domain knowledge and specialized capabilities for each sector
- 🤖 **Intelligent Routing** - Automatic query routing to appropriate specialized agents  
- 🤝 **Multi-Agent Collaboration** - Coordinated responses from multiple expert agents
- 📊 **Regulatory Compliance** - Built-in regulatory guidance and compliance requirements
- 🔧 **Consistent Architecture** - Standardized patterns across all industry modules
- 📈 **Scalable Design** - Easy to extend and customize for specific needs

## 📦 Installation

```bash
pip install sasefied
```

### Optional Dependencies

For enhanced web scraping capabilities:
```bash
pip install sasefied[scraping]
```

For web interface:
```bash
pip install sasefied[web]
```

## 🎯 Quick Start

### Basic Agent Usage

```python
from sasefied.agents import DeepSearchAgent
from langchain_openai import ChatOpenAI

# Initialize LLM
llm = ChatOpenAI(model="gpt-4")

# Create a deep search agent
search_agent = DeepSearchAgent(llm=llm)

# Use the agent
result = search_agent.invoke([
    {"role": "user", "content": "Research the latest developments in quantum computing"}
])
print(result["messages"][-1].content)
```

### Industry-Specific Agents

```python
from sasefied.industry.airlines import create_passenger_service_agent
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4")

# Create airline passenger service agent
agent = create_passenger_service_agent(llm=llm)

# Handle passenger inquiry
response = agent.invoke([
    {"role": "user", "content": "What are the baggage policies for international flights?"}
])
```

### Multi-Agent Agentic Systems

```python
from sasefied.industry.airlines import create_airline_orchestrator
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4")

# Create complete airline management system
orchestrator = create_airline_orchestrator(llm)

# Coordinate multiple agents for complex operations
result = orchestrator.handle_flight_disruption(
    flight_id="AA123",
    issue="weather_delay",
    passengers=150
)
# Automatically coordinates: Operations, Crew, Passenger Service, Revenue Management
```

### Using the Prompt Hub

```python
from sasefied.hub import AgentPromptExplorerHub

# Initialize the hub
hub = AgentPromptExplorerHub()

# Search for prompts
prompts = hub.search_prompts("customer service", industry="retail")

# Export prompts
hub.export_prompts(prompts, format="json", output_file="customer_prompts.json")
```

### CLI Usage

```bash
# Explore available prompts
sasefied-hub explore

# Search for specific prompts
sasefied-hub search "revenue management" --industry airlines

# Export prompts
sasefied-hub export --industry healthcare --format yaml
```

## 🏗️ Architecture

```
sasefied/
├── agents/                 # Core agent framework
│   ├── base.py            # BaseAgent class
│   └── deep_search.py     # DeepSearchAgent implementation
├── industry/              # Industry-specific agents
│   ├── airlines/          # Airline industry agents
│   ├── ev_batteries/      # EV battery industry agents
│   └── fruits/            # Agriculture industry agents
├── hub/                   # Prompt management system
│   ├── core/              # Core models and repository
│   ├── cli.py             # Command-line interface
│   ├── web.py             # Web interface
│   └── hub.py             # Main hub functionality
├── tools/                 # Utility tools
│   └── http.py            # HTTP request tool
└── agentic_systems/       # Multi-agent orchestration
```

## 🔧 Configuration

### Environment Variables

```bash
# OpenAI API (if using OpenAI models)
OPENAI_API_KEY=your_api_key_here

# Optional: Custom model configurations
DEFAULT_MODEL=gpt-4
DEFAULT_TEMPERATURE=0.7
```

### Custom Agent Development

```python
from sasefied.agents.base import BaseAgent
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI

class CustomAgent(BaseAgent):
    def __init__(self, llm: ChatOpenAI, tools: List[BaseTool] = None):
        super().__init__(
            name="CustomAgent",
            description="Your custom agent description",
            tools=tools or [],
            llm=llm
        )
    
    def get_system_prompt(self) -> str:
        return "You are a specialized agent for..."
```

## 📚 Documentation

- [API Reference](docs/api.md)
- [Agent Development Guide](docs/agent-development.md)
- [Industry Solutions](docs/industry-solutions.md)
- [Prompt Hub Guide](docs/prompt-hub.md)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
git clone https://github.com/your-org/sasefied.git
cd sasefied
pip install -e ".[dev]"
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- 📖 [Documentation](docs/)
- 🐛 [Issue Tracker](https://github.com/your-org/sasefied/issues)
- 💬 [Discussions](https://github.com/your-org/sasefied/discussions)

## 🌟 Roadmap

- [ ] Additional industry modules (Healthcare, Finance, Manufacturing)
- [ ] Advanced orchestration patterns
- [ ] Performance monitoring and analytics
- [ ] Integration with more LLM providers
- [ ] Enhanced web scraping capabilities
- [ ] Agent marketplace and sharing platform

## 🏆 Acknowledgments

Built with:
- [LangChain](https://langchain.com/) - LLM framework
- [LangGraph](https://langchain-ai.github.io/langgraph/) - Agent orchestration
- [DuckDuckGo](https://duckduckgo.com/) - Search integration

---

**Sasefied** - Empowering the next generation of intelligent agents.