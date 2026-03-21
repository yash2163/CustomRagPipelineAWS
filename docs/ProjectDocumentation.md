# Project Documentation: Metadata-Filtered RAG Agent on AWS

## 1. Project Overview & Scope

The project aims to build a **Metadata-Filtered RAG Agent on AWS**. It automates the ingestion of structured recipe data, converts it into a format suitable for Bedrock Knowledge Bases, and provides an intelligent interface for users to query recipes based on both:

- **Semantic meaning** (e.g., "spicy food")
- **Strict constraints** (e.g., "cook time < 20 mins")

### Core Scope

1. **Automated Ingestion**: A pipeline that reacts to new S3 uploads and transforms them
2. **Hybrid Search**: Custom Lambda logic to combine S3 metadata filtering with vector similarity
3. **Conversational Logic**: A Bedrock Agent that manages multi-turn dialogue to collect missing filter parameters

---

## 2. Architecture & Service Flow

### Stage A: The Automated Data Pipeline

```
Landing Zone (S3 Bucket A)
    ↓ (User uploads recipes.csv)
S3 Event Notification
    ↓
AWS Lambda / Glue Job (Transformer)
    ↓
Transformation:
  • Parses CSV
  • Converts "20 mins" → 20 integer
  • Generates: recipe_N.txt + recipe_N.txt.metadata.json
    ↓
Knowledge Base Source (S3 Bucket B)
    ↓ (API call triggers sync)
Bedrock Knowledge Base ↔ Vector Serverless
```

**Key Steps:**
- User uploads `recipes.csv` to Landing Zone
- S3 Event Notification triggers Lambda Transformer
- **Transformation Process:**
  - Parses CSV data
  - Converts time strings ("20 mins", "1 hr") into integer minutes
  - Generates pairs of files for each row:
    - `recipe_N.txt` (content)
    - `recipe_N.txt.metadata.json` (metadata)
- Transformer saves files to Knowledge Base Source (S3 Bucket B)
- Bedrock Knowledge Base syncs with vector serverless

### Stage B: The Intelligent Agent (Inference)

```
User Input
    ↓
Bedrock Agent
    ↓
┌─────────────────────────────────────────────┐
│ Case 1: Parameters Found                     │
│ Extract filters → Call Action Group Lambda   │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│ Case 2: Parameters Missing                  │
│ Ask clarifying questions to user            │
└─────────────────────────────────────────────┘
    ↓
Action Group Lambda
    ↓
Construct Query: WHERE total_time_min <= X AND vector_matches(query)
    ↓
Query S3 Vector Serverless
    ↓
Return Recipe Chunks → Bedrock Agent
    ↓
Format Final Answer → User
```

**Flow:**
1. User Input: "I want a chicken recipe that takes less than 30 minutes"
2. Bedrock Agent identifies:
   - Query: "chicken"
   - Constraint: "30 minutes"
3. Calls Action Group Lambda with extracted parameters
4. Lambda constructs metadata-filtered query
5. Queries S3 Vector Serverless
6. Returns relevant recipe chunks
7. Agent formats and presents final answer to user

---

## 3. Flow Case Scenarios

| User Scenario | Agent Action | Lambda Action | Response |
|---------------|--------------|---------------|----------|
| **Direct Filter:** "Recipes under 15m" | Extracts `max_time=15` | Applies Range filter in S3 | Returns matching recipes |
| **No Filter:** "Tell me about Curry" | Passes `filter=null` | Performs standard Vector Search only | Returns all curry-related recipes |
| **Vague Filter:** "A fast recipe" | Ask follow-up: "What is your max cook time?" | Waits for next turn | Collects constraint info |
| **Too Restrictive:** "Under 1 min" | Receives 0 results from Lambda | Triggers error handling | "I couldn't find anything that fast. Try increasing the time limit." |

---

## 4. Key Design Principles

- **Precision First**: Metadata filtering happens before semantic search to ensure exact constraints are met
- **User-Centric**: Multi-turn dialogue collects missing parameters naturally
- **Scalability**: Serverless architecture scales automatically
- **Transparency**: Always cite recipe sources from S3

---

## 5. Implementation Notes

- Time normalization is critical for consistent filtering
- Metadata JSON sidecars enable rich filtering without modifying the main knowledge base
- Lambda functions are optimized for quick parameter extraction and query construction
- Bedrock Agent uses the OpenAPI schema to understand available filters
