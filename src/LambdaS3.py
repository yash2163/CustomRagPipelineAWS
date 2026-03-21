# lambda function to get data from S3 bucket and show in the logs. Used this to test connection with S3 and pandas layer in lambda.

import boto3
import pandas as pd
import io

s3 = boto3.client('s3')

def lambda_handler(event, context):
    bucket = "recipes-landing-zone-2163"
    key = "train_recipes_80.csv"
    
    # 1. Fetch file from S3
    response = s3.get_object(Bucket=bucket, Key=key)
    
    # 2. Load into pandas
    df = pd.read_csv(io.BytesIO(response['Body'].read()))
    
    # 3. Print first 5 rows (for logs)
    print("===== DATA PREVIEW =====")
    print(df.head())
    
    # 4. Convert to JSON-safe format
    data = df.head().to_dict(orient="records")
    
    return {
        "statusCode": 200,
        "body": data
    }