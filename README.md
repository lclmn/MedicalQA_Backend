# Medical QA System - LangChain Refactor

This directory contains the refactored backend for the Medical Question Answering system. It now utilizes **LangChain**, **Neo4j**, and **DeepSeek LLM** to provide accurate answers with a fallback mechanism.

## Key Features

1.  **GraphCypherQAChain**: Automatically translates natural language questions into Cypher queries to query the Neo4j database.
2.  **DeepSeek LLM Integration**: Uses DeepSeek-V3 (via OpenAI compatibility) for both Cypher generation and answer elaboration.
3.  **Smart Fallback**: 
    -   If the Knowledge Graph (KG) contains the answer, the LLM elaborates on it professionally.
    -   If the KG does not have the answer (or returns "I don't know"), the system automatically fails back to the LLM's general medical knowledge.
4.  **Schema Awareness**: Uses a predefined schema to ensure generated Cypher queries are valid and structurally correct.

## Setup

1.  **Dependencies**:
    Ensure the following packages are installed (see `requirements.txt`):
    ```bash
    pip install -r requirements.txt
    ```
    Key new packages: `langchain`, `langchain-community`, `langchain-openai`, `langchain-neo4j`.

2.  **Neo4j**:
    -   Ensure Neo4j is running locally on `bolt://localhost:7687`.
    -   Credentials: `neo4j` / `password`.
    -   Data should be imported using `python import_to_neo4j.py`.

3.  **Configuration**:
    -   API keys and DB credentials are currently configured in `langchain_qa.py`.

## Running the Server

Run the Flask application as usual:

```bash
python app.py
```
Or use the batch script:
```bash
run_backend.bat
```

The server runs on `http://127.0.0.1:5001`.

## Usage

-   **Endpoint**: `GET /question?question=...`
-   **Example**: `http://127.0.0.1:5001/question?question=感冒有哪些症状？`

## Code Structure

-   `app.py`: Main Flask entry point. Delegates QA logic to `langchain_qa.py`.
-   `langchain_qa.py`: **[NEW]** Core logic. Initializes the LangChain graph and LLM, defines prompts, and handles fallback logic.
-   `import_to_neo4j.py`: Scripts to load CSV data into Neo4j.
