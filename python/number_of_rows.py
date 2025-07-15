import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ItalianQuizQuestions')

def count_all_items():
    total = 0
    response = table.scan()
    items = response.get('Items', [])
    total += len(items)

    # Handle pagination if needed
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items = response.get('Items', [])
        total += len(items)

    print(f"📊 Total number of questions in the table: {total}")

count_all_items()
