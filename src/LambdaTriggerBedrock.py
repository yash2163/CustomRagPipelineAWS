import boto3
import json
import uuid

# Initialize the client
bedrock_runtime = boto3.client('bedrock-agent-runtime')

def lambda_handler(event, context):
    # 1. Parse Input (Handle both direct console test and API Gateway)
    if isinstance(event.get('body'), str):
        body = json.loads(event['body'])
    else:
        body = event
        
    user_input = body.get('message', '')
    # Use existing sessionId or create a new one for memory management
    session_id = body.get('sessionId', str(uuid.uuid4()))
    
    agent_id = 'PEJWG79PPN' # Replace with your Agent ID
    agent_alias_id = 'TG7VCMSJLQ' # Replace with your Alias ID (or 'TSTALIASID')

    try:
        # 2. Invoke the Agent
        response = bedrock_runtime.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionId=session_id,
            inputText=user_input
        )

        # 3. Process the Response Stream
        completion = ""
        for event in response.get('completion'):
            chunk = event.get('chunk')
            if chunk:
                completion += chunk.get('bytes').decode('utf-8')

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'answer': completion,
                'sessionId': session_id
            })
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }