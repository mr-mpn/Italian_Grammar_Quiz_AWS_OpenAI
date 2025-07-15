import boto3
import uuid

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ItalianQuizQuestions')

print("Connected to DynamoDB table:", table.name)

def load_questions_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        for i, line in enumerate(file):
            parts = line.strip().split('|')
            if len(parts) != 7:
                print(f"Skipping malformed line {i+1}: {line}")
                continue
            
            level = int(parts[0])
            question_id = f"lvl{level}-q{i+1:03}"
            question_text = parts[1]
            choices = parts[2:6]
            correct_choice_number = int(parts[6])

            item = {
                'level': level,
                'question_id': question_id,
                'question_text': question_text,
                'choice_1': choices[0],
                'choice_2': choices[1],
                'choice_3': choices[2],
                'choice_4': choices[3],
                'correct_choice_number': correct_choice_number
            }

            table.put_item(Item=item)
            print(f"Inserted question {question_id}")

# Run it
load_questions_from_file('quiz_questions.txt')
