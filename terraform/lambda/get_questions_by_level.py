import boto3
import json
import os
from boto3.dynamodb.conditions import Key
from decimal import Decimal
from boto3.dynamodb.types import TypeDeserializer

dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('DDB_TABLE', 'ItalianQuizQuestions')
table = dynamodb.Table(table_name)

def convert_decimal(obj):
    """Recursively convert Decimal objects to int or float."""
    if isinstance(obj, list):
        return [convert_decimal(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    else:
        return obj

def lambda_handler(event, context):
    print("📥 Incoming event:", json.dumps(event))

    try:
        path_params = event.get('pathParameters', {})
        level = int(path_params.get('level'))
    except Exception as e:
        print("⚠️ Failed to get level:", str(e))
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing or invalid level'})
        }

    try:
        response = table.query(
            KeyConditionExpression=Key('level').eq(level)
        )
        questions = response.get('Items', [])
        print(f"✅ Found {len(questions)} questions")

        # Remove correct answer before sending to frontend
        for q in questions:
            q.pop('correct_choice_number', None)

        # Convert Decimal to JSON-safe
        questions_clean = convert_decimal(questions)

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS"},
            'body': json.dumps({'level': level, 'questions': questions_clean})
        }

    except Exception as e:
        print("🔥 DynamoDB error:", str(e))
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal error', 'details': str(e)})
        }
