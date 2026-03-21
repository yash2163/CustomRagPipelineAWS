# Metadata-Filtered Recipe RAG System

## Objective

Build a specialized Retrieval-Augmented Generation (RAG) system that allows users to query structured data using both semantic meaning (natural language) and strict constraints (metadata filters).

---

## Problem Statement

Standard RAG systems often struggle with "hard" constraints (e.g., "Find a recipe under 30 minutes"). An LLM might find a recipe that mentions "30 minutes" in the text but actually takes 2 hours to cook.

## Why This Architecture?

We chose the "Lambda-as-a-Tool" approach because:

- **Precision**: Forces the Vector Store to filter by exact numerical values before performing semantic search
- **Automation**: Ensures any new CSV data uploaded is automatically indexed without manual intervention
- **Cost-Efficiency**: Uses S3 as primary store and triggers compute only when needed for low-cost, serverless operation

---

## Technical Workflow

### Stage A: Automated Ingestion Pipeline

1. **Landing Zone**: Raw structured data (CSV) is uploaded to a Source S3 Bucket
2. **Transformation (LambdaS3)**: S3 Event Trigger fires a Lambda function that:
   - Parses the CSV
   - Normalizes data (e.g., converting "1 hr" to 60 minutes)
   - Splits each row into a `.txt` content file and `.metadata.json` sidecar file
3. **Knowledge Base (KB) Sync**: Files are saved to a Destination S3 Bucket, which serves as the data source for Amazon Bedrock Knowledge Base

### Stage B: Intelligent Retrieval Layer

1. **User Intent Extraction**: User asks a question via the Bedrock Agent
2. **Parameter Mapping**: Using an OpenAPI Schema, the Agent identifies if the user mentioned a constraint (e.g., `max_cook_time`)
3. **The Action Group (BedrockTriggerLambdaQueryKB)**: Instead of blind search, the Agent triggers this Lambda, passing extracted filters as parameters
4. **Metadata-Filtered Query**: Lambda executes a retrieve call to KB, injecting a `retrievalConfiguration` that limits search to only files matching user's numeric constraints

### Stage C: Final Response

1. **Context Injection**: Lambda returns filtered, relevant recipe chunks back to Bedrock Agent
2. **Grounded Answer**: Bedrock synthesizes the final response, citing specific S3 sources for transparency

---

## Key Components

| Component | Role | Logic |
|-----------|------|-------|
| S3 Landing | Trigger | Entry point for raw data |
| LambdaS3 ETL | Transform | Converts "Human" time strings to "Machine" integers |
| Bedrock KB | Vector Index | Stores embeddings and manages similarity search |
| Bedrock Agent | Orchestrator | Decides when to filter vs. when to ask for clarification |
| Action Lambda | Bridge | Translates Agent intent into structured KB filters |

---

## Project Structure

```
AWS_RAG_Project1/
├── README.md                                    # This file
├── docs/                                        # Documentation
│   ├── HowToSetUpCustomRagPipeline.md
│   ├── ProjectDocumentation.txt
│   └── APISchemaBedrockForLambdaTrigger.yaml
├── src/                                         # Source code
│   ├── LambdaS3.py                             # ETL Lambda for data transformation
│   └── BedrockTriggerLambdaQueryKB.py          # Query Lambda for KB retrieval
├── config/                                      # Configuration files
│   └── AgentPrompt.txt                         # Bedrock Agent prompt
├── data/                                        # Data files
│   ├── RecipeDataset/
│   │   ├── recipes.csv
│   │   ├── test_recipes.csv
│   │   ├── train_recipes_80.csv
│   │   └── test_recipes_20.csv
│   └── analysis.ipynb
└── .venv/                                       # Virtual environment
```

---

## Getting Started

1. **Set up your AWS environment** with proper credentials for S3, Lambda, and Bedrock
2. **Upload raw recipe data** to the Source S3 Bucket
3. **LambdaS3 will automatically trigger** to process and normalize the data
4. **Configure the Bedrock Agent** with the provided action schema
5. **Query using natural language** with optional metadata constraints

---

## Files Overview

- **LambdaS3.py**: Handles CSV ingestion, data normalization, and metadata extraction
- **BedrockTriggerLambdaQueryKB.py**: Executes filtered queries on the Knowledge Base
- **APISchemaBedrockForLambdaTrigger.yaml**: OpenAPI schema defining the agent's action group
- **AgentPrompt.txt**: System prompt for the Bedrock Agent

---

## Notes

- Metadata filtering happens at the KB query level, ensuring precision
- Time formats are normalized to minutes for consistent filtering
- All data is stored with sidecar metadata files for rich context
