import json
import boto3
import openai
import os
from boto3.dynamodb.conditions import Key
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['DDB_TABLE'])

def decimal_to_native(obj):
    if isinstance(obj, list):
        return [decimal_to_native(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: decimal_to_native(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    else:
        return obj

def get_openai_explanation(question_text, user_answer, correct_answer, choices):
    prompt = (
        f"Explain in English and in maximum 3 sentences very simply the Italian grammar of why the correct answer to the question:\n\n"
        f"'{question_text}'\n\n"
        f"is choice number {correct_answer} ({choices[correct_answer - 1]}), "
        f"and the user's answer was choice number {user_answer} ({choices[user_answer - 1]}). "
        f"Be clear and concise."
    )
    print(f"🤖 Calling OpenAI for question explanation:\n{prompt}\n")
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.7,
        )
        explanation = response['choices'][0]['message']['content'].strip()
        print(f"📝 OpenAI response: {explanation[:100]}...")
        return explanation
    except Exception as e:
        print(f"❌ OpenAI API error: {str(e)}")
        return "No explanation available due to API error."

def lambda_handler(event, context):
    print(f"📥 Received event: {json.dumps(event)}")
    try:
        openai.api_key = os.environ['OPENAI_API_KEY']
        print("🔑 OpenAI API key loaded.")

        level = int(event["pathParameters"]["level"])
        print(f"🎯 Processing quiz level: {level}")

        body = json.loads(event.get("body", "{}"))
        answer_list = body.get("answers", [])
        print(f"✉️ Received {len(answer_list)} answers from user.")

        response = table.query(
            KeyConditionExpression=Key("level").eq(level)
        )
        questions = response["Items"]
        print(f"📚 Fetched {len(questions)} questions from DynamoDB.")

        question_map = {q["question_id"]: q for q in questions}

        total = len(answer_list)
        correct = 0
        results = {}

        for entry in answer_list:
            qid = entry.get("question_id")
            user_answer = entry.get("answer")
            print(f"🧐 Grading question: {qid} | user_answer: {user_answer}")

            if not qid or qid not in question_map:
                print(f"⚠️ Question ID {qid} not found in DB.")
                results[qid] = {"status": "not found"}
                continue

            question = question_map[qid]
            correct_answer = int(question["correct_choice_number"])
            choices = [
                question["choice_1"],
                question["choice_2"],
                question["choice_3"],
                question["choice_4"],
            ]

            is_correct = int(user_answer) == correct_answer
            if is_correct:
                correct += 1
                explanation = ""  # Skip explanation for correct answers
            else:
                explanation = get_openai_explanation(
                    question_text=question["question_text"],
                    user_answer=int(user_answer),
                    correct_answer=correct_answer,
                    choices=choices
                )

            results[qid] = {
                "your_answer": int(user_answer),
                "correct_answer": correct_answer,
                "is_correct": is_correct,
                "openai": explanation
            }

        print(f"🏆 User scored {correct} out of {total}.")

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "message": "Quiz graded with explanations from OpenAI",
                "score": f"{correct}/{total}",
                "results": decimal_to_native(results)
            })
        }

    except Exception as e:
        print(f"🔥 Lambda failed: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Internal Server Error",
                "details": str(e)
            })
        }
