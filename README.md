# Metadata-Filtered Recipe RAG System

## 🎯 Objective

Build a specialized **Retrieval-Augmented Generation (RAG) system** that allows users to query structured data using both semantic meaning (natural language) and strict constraints (metadata filters).

## 💡 Problem Statement

Standard RAG systems often struggle with "hard" constraints (e.g., "Find a recipe under 30 minutes"). An LLM might find a recipe that mentions "30 minutes" in the text but actually takes 2 hours to cook. This project solves that boundary issue with an intelligent Lambda-as-a-Tool metadata filtering architecture.

---

## 🏗️ Why This Architecture?

We chose the **"Lambda-as-a-Tool"** approach because:
- **Precision**: Forces the Vector Store to filter by exact numerical values before performing semantic search.
- **Automation**: Ensures any new CSV data uploaded is automatically indexed without manual intervention.
- **Cost-Efficiency**: Uses S3 as the primary store and triggers compute only when needed for a low-cost, serverless footprint.

---

## 🚀 Architecture & End-to-End Flow

The pipeline is split into an offline data ingestion pipeline and an online conversational retrieval pipeline.

### Stage A: The Automated Ingestion Pipeline
1. **Landing Zone**: Raw structured data (`recipes.csv`) is uploaded to a Source S3 Bucket.
2. **Transformation (`LambdaS3.py`)**: An S3 Event Notification fires an AWS Lambda function that:
   - Parses the CSV
   - Normalizes data (e.g., converting "1 hr" to 60 integer minutes)
   - Splits each row into a `.txt` content file and `.metadata.json` sidecar file
3. **Knowledge Base (KB) Sync**: Files are saved to a Destination S3 Bucket, which serves as the data source for the Amazon Bedrock Knowledge Base. 

### Stage B: The Intelligent Retrieval Layer
1. **Frontend Request**: The user submits a query through the web interface (`index.html` hosted on S3).
2. **API Gateway Bridge**: The static frontend sends a POST request to an API Gateway endpoint.
3. **Agent Trigger (`LambdaTriggerBedrock.py`)**: API Gateway invokes a Lambda that wraps and passes the user intent to the Bedrock Agent.
4. **Parameter Mapping**: Using the injected OpenAPI Schema, the Bedrock Agent identifies if the user mentioned a constraint (e.g., `max_cook_time`).
5. **The Action Group (`BedrockTriggerLambdaQueryKB.py`)**: Instead of a blind vector search, the Agent triggers this Lambda, passing the extracted filters as parameters.
6. **Metadata-Filtered Query**: The Action Group Lambda executes a `retrieve` call to the KB, injecting a `retrievalConfiguration` that limits the vector search exclusively to files that match the exact numeric constraints.

### Stage C: Final Response
1. **Context Injection**: The Action Group Lambda returns the strictly filtered, relevant recipe chunks back to the Bedrock Agent.
2. **Grounded Answer**: Bedrock synthesizes the final conversational response, citing the specific S3 chunk IDs and source URIs for total transparency.
3. **Delivery to User**: The response traverses back through `LambdaTriggerBedrock.py` -> API Gateway -> `index.html`.

---

## 🚦 Flow Case Scenarios

The Bedrock Agent uses multi-turn capabilities to guarantee precision:

| User Scenario | Agent Action | Lambda Action | Final Response |
|---------------|--------------|---------------|----------------|
| **Direct Filter:** "Recipes under 15m" | Extracts `max_prep_time=15` | Applies Range filter in KB query | Returns accurately vetted matching recipes |
| **No Filter:** "Tell me about Curry" | Passes `filter=null` | Performs standard Vector Search | Returns all curry-related recipes |
| **Vague Filter:** "A fast recipe" | Ask follow-up: *"What is your max cook time?"* | Waits for next turn | Collects exact integer constraint |
| **Too Restrictive:** "Under 1 min" | Receives `0` results from Lambda | Triggers error handling protocol | *"I couldn't find anything that fast. Try increasing the time limit."* |

---

## 🧩 Key Components Summary

| Component | Role | Logic & Function |
|-----------|------|------------------|
| **S3 Landing Bucket** | Trigger | Entry point for raw, newly uploaded CSV data. |
| **`LambdaS3.py` (ETL Lambda)** | Transform | Converts "Human" time strings to "Machine" integers and generates JSON sidecars. |
| **Bedrock Knowledge Base** | Vector Index | Stores embeddings, S3 URIs, and manages similarity searches. |
| **Bedrock Agent** | Orchestrator | Interprets intent, manages multi-turn dialogue, synthesizes final answers. |
| **`BedrockTriggerLambdaQueryKB.py`** | Action Bridge | Translates Agent intent into structured KB metric filters. |
| **API Gateway + `LambdaTriggerBedrock.py`**| Client Bridge | Connects S3 static HTML endpoints securely to Bedrock. |

---

## 📂 Project Structure

```
AWS_RAG_Project1/
├── README.md                                    # This centralized documentation
├── index.html                                   # Simple UI frontend (hosted via S3)
├── docs/                                        
│   └── APISchemaBedrockForLambdaTrigger.yaml    # OpenAPI Agent Action Group definition
├── src/                                         
│   ├── LambdaS3.py                              # ETL Lambda for offline data transformation
│   ├── BedrockTriggerLambdaQueryKB.py           # Lambda Action Group for strict KB retrieval
│   └── LambdaTriggerBedrock.py                  # API Gateway connected Bedrock entrypoint
├── config/                                      
│   └── AgentPrompt.txt                          # System prompt for the Bedrock Agent orchestration
├── RecipeDataset/                               
│   └── [Recipe CSV files handling]
└── analysis.ipynb                               # Dataset analytics notebook
```

---

## 🛠️ Getting Started / Setup Guide

1. **Deploy Frontend & Gateway**:
   - Host `index.html` in a public S3 Bucket configured for static website hosting.
   - Set up an API Gateway connected to `LambdaTriggerBedrock.py`. Ensure CORS headers are enabled.
   - Update `API_URL` in `index.html` with your deployed API Gateway endpoint.
2. **Set up Ingestion Sandbox**: 
   - Create Source & Destination S3 buckets.
   - Configure S3 Event Notifications on the Source Bucket to trigger the `LambdaS3.py` function.
3. **Provision the Knowledge Base**:
   - Create an Amazon Bedrock Knowledge Base and point the data source to the Destination S3 bucket (where the populated `<file>.txt` and `<file>.metadata.json` pairs reside).
   - Sync the Knowledge Base.
4. **Configure the Bedrock Agent**:
   - Create a new interactive Bedrock Agent.
   - Inject the prompt found in `config/AgentPrompt.txt`.
   - Create an Action Group pointing to the `BedrockTriggerLambdaQueryKB.py` function and utilizing the `docs/APISchemaBedrockForLambdaTrigger.yaml` schema.
5. **Start Querying**:
   - Upload new recipes to the Landing Zone, wait to sync, and ask the frontend naturally vague or strict queries to see the system in action!

---

## 📝 Implementation Notes

- Metadata filtering occurs structurally inside the KB via injecting `retrievalConfiguration` -> `filter` -> `lessThanOrEquals` at query execution, rather than post-search validation. This guarantees no false-positives reach the LLM.
- **`AgentPrompt.txt`** requires the Agent to actively refuse to guess if a user asks for "fast foods" and mandate numeric classification. 
- All conversational answers rigorously map back back to `Location > s3Location > uri` chunk extracts so the LLM is forcibly grounded.
