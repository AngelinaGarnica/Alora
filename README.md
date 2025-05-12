# 🤖 ALORA - Reasoning SQL Agent with Interactive Plotly Charts

This project implements an intelligent agent that:
- Generates SQL queries from natural language
- Uses tools to explore the database (list/describe tables, find similar names)
- Executes the query and validates the results with the user
- Offers to automatically generate a chart (using **Plotly**)

All of this using **LangChain**, **LangGraph**, and an LLM like OpenAI or Gemini (Google Generative AI).

---

## 🚀 Usage Example

User: How many artist are there??
🔁 The agent analyzes the tables, generates the SQL query, executes it, and displays the results.
🤖 Result: There are 5 employees in Calgary, 1 in Edmonton, and 2 in Lethbridge.
✅ User approves the data.
📊 The agent offers to generate an interactive chart with Plotly.

---

## ⚙️ Requirements

pip install -r requirements.txt

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

ALORA/
├── run.py               # Script to run the agent
├── requirements.txt     # Dependencies
├── README.md            
├── data/
│   └── sample.db        # Sample database
└── src/
    ├── config.py        # Configuration (LLM, DB, logging)
    ├── prompts.py       # Prompt templates
    ├── tools.py         # Tools (e.g., SQL execution, chart generation)
    ├── nodes.py         # Graph Nodes (reasoning, approval, etc.)
    └── graph.py         # Agent's LangGraph flow


---
## How to run

To run the agent, use the `run.py` script from your terminal.

**Provide a question directly as an argument:**

    ```bash
    python run.py "Your question here"
    ```
    
This will execute the agent with your specified question, and it will output the results, including any generated charts if applicable.

**Example:**
    
    ```bash
    python run.py "How many albums do artists have on average?" 
    ```

---
## 📜 License

This project is licensed under the MIT License. See the `LICENSE.md` file for details.

---
## 🤝 Contributing

Contributions are welcome! If you'd like to contribute, please follow these steps:

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/your-feature-name`).
3.  Make your changes and commit them (`git commit -m 'Add some feature'`).
4.  Push to the branch (`git push origin feature/your-feature-name`).
5.  Open a Pull Request.