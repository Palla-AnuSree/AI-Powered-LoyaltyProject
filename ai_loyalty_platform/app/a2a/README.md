# A2A implementation plan
Use A2A when independent agent services need to discover and communicate with one another.
Suggested services:
- Support Agent
- Order Agent
- Loyalty Agent
- Redemption Investigation Agent

Implement Agent Cards, authenticated task submission, task status updates, message exchange,
timeouts, retries, and trace/correlation IDs. LangGraph can orchestrate local workflows;
A2A is for communication across separately deployed agents.
