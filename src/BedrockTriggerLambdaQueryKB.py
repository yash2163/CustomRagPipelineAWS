# This is an lambda function that serves as a Bedrock Agent Action for querying a Knowledge Base with dynamic filters based on parameters passed from the Agent. It retrieves relevant documents from the Knowledge Base and formats the response to include both the content and metadata (like source and chunk ID) for each retrieved document.

import boto3
import os

bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')
KNOWLEDGE_BASE_ID = os.environ.get('KNOWLEDGE_BASE_ID')

def lambda_handler(event, context):
    query_text = event.get('inputText', '')
    params = event.get('parameters', [])
    
    # 1. Extract all potential parameters from the Agent
    # Note: Ensure these names match your Agent's Action Group parameter names
    filters_found = []
    
    mapping = {
        'max_prep_time': 'prep_time_min',
        'max_cook_time': 'cook_time_min',
        'max_total_time': 'total_time_min'
    }

    for p in params:
        if p['name'] in mapping and p['value']:
            filters_found.append({
                "lessThanOrEquals": {
                    "key": mapping[p['name']],
                    "value": int(p['value'])
                }
            })

    # 2. Build Retrieval Configuration
    retrieval_config = {
        "vectorSearchConfiguration": {
            "numberOfResults": 2
        }
    }

    # 3. Apply Filters (Single or Combined)
    if len(filters_found) == 1:
        retrieval_config["vectorSearchConfiguration"]["filter"] = filters_found[0]
    elif len(filters_found) > 1:
        retrieval_config["vectorSearchConfiguration"]["filter"] = {
            "andAll": filters_found
        }

    try:
        # 4. Execute Retrieval
        res = bedrock_agent_runtime.retrieve(
            knowledgeBaseId=KNOWLEDGE_BASE_ID,
            retrievalConfiguration=retrieval_config,
            retrievalQuery={"text": query_text}
        )

        formatted_results = []
        for doc in res['retrievalResults']:
            content = doc['content']['text']
            # Extract S3 URI from the location object
            s3_uri = doc.get('location', {}).get('s3Location', {}).get('uri', 'Unknown Source')
            # Extract Internal Chunk ID
            chunk_id = doc.get('metadata', {}).get('x-amz-bedrock-kb-chunk-id', 'N/A')
            
            formatted_results.append(
                f"SOURCE: {s3_uri}\nCHUNK_ID: {chunk_id}\nCONTENT: {content}"
            )

        response_text = "\n\n---\n\n".join(formatted_results) if formatted_results else "No matches found."

        return {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": event['actionGroup'],
                "apiPath": event['apiPath'],
                "httpMethod": event['httpMethod'],
                "httpStatusCode": 200,
                "responseBody": {
                    "TEXT": {"body": response_text}
                }
            }
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": event['actionGroup'],
                "apiPath": event['apiPath'],
                "httpMethod": event['httpMethod'],
                "httpStatusCode": 500,
                "responseBody": {
                    "TEXT": {"body": f"Search Error: {str(e)}"}
                }
            }
        }
