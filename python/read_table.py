import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ItalianQuizQuestions')
print(f"📊 Item count (cached): {table.item_count}")

def print_all_questions_by_level():
    for level in range(1, 11):
        print(f"\n📘 Level {level} Questions:")
        response = table.query(
            KeyConditionExpression=Key('level').eq(level)
        )
        items = response['Items']
        for item in items:
            print(f"- {item['question_id']}: {item['question_text']}")
            print(f"  1) {item['choice_1']}")
            print(f"  2) {item['choice_2']}")
            print(f"  3) {item['choice_3']}")
            print(f"  4) {item['choice_4']}")
            print(f"  ✅ Correct: {item['correct_choice_number']}\n")

print_all_questions_by_level()
print(f"📊 Item count (cached): {table.item_count}")

