# 🤖 ALORA - Reasoning SQL Agent with Interactive Plotly Charts

This project implements an intelligent agent that: <br>
- Generates SQL queries from natural language <br>
- Uses tools to explore the database (list/describe tables, find similar names) <br>
- Executes the query and validates the results with the user <br>
- Offers to automatically generate a chart (using **Plotly**) <br>

All of this using **LangChain**, **LangGraph**, and an LLM like OpenAI or Gemini (Google Generative AI).

---

## 🚀 Usage Example

User: How many artist are there?? <br>
🔁 The agent analyzes the tables, generates the SQL query, executes it, and displays the results.<br>
🤖 Result: There are 5 employees in Calgary, 1 in Edmonton, and 2 in Lethbridge.<br>
✅ User approves the data.<br>
📊 The agent offers to generate an interactive chart with Plotly.<br>

---

## ⚙️ Requirements

```bash
pip install -r requirements.txt
```
---
## 🛠️ Configuration

Before running the agent, you'll need to configure your API keys for the Large Language Model (LLM) you intend to use (OpenAI or Gemini).

1.  **API Keys**:
    *   Modify the `src/config.py` file to include your API keys.
    *   Alternatively, you can set them as environment variables (e.g., `OPENAI_API_KEY`, `GOOGLE_API_KEY`). Check `src/config.py` for the specific variable names it expects.

2.  **Database**:
    *   The project uses a sample SQLite database located at `data/sample.db`. If you want to use a different database, update the connection details in `src/config.py`.
---
## 📂 Project Structure

ALORA/ <br>
├── run.py                   # Script to run the agent <br>
├── requirements.txt         # Dependencies <br>
├── README.md <br>         
├── data/ <br>
│   └── sample.db            # Sample database <br>
└── src/ <br>
    ├── config.py            # Configuration (LLM, DB, logging) <br>
    ├── prompts.py           # Prompt templates <br>
    ├── tools.py             # Tools (e.g., SQL execution, chart generation) <br>
    ├── nodes.py             # Graph Nodes (reasoning, approval, etc.) <br>
    └── graph.py             # Agent's LangGraph flow <br>


---
## How to run <br>

To run the agent, use the `run.py` script from your terminal. <br>

**Provide a question directly as an argument:** <br>

```bash
python run.py "Your question here"
```
    
This will execute the agent with your specified question, and it will output the results, including any generated charts if applicable. <br>

**Example:** <br>
    
```bash
python run.py "How many albums do artists have on average?" 
```

---
## 📜 License <br>

This project is licensed under the MIT License. See the `LICENSE.md` file for details.

---
## 🤝 Contributing <br>

Contributions are welcome! If you'd like to contribute, please follow these steps:

1.  Fork the repository. <br>
2.  Create a new branch (`git checkout -b feature/your-feature-name`). <br>
3.  Make your changes and commit them (`git commit -m 'Add some feature'`). <br>
4.  Push to the branch (`git push origin feature/your-feature-name`). <br>
5.  Open a Pull Request. <br>
