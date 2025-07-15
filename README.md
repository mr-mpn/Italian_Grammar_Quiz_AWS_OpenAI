# Italian_grammar_quiz_aws
<img width="600" height="326" alt="openai-aws-600x326" src="https://github.com/user-attachments/assets/7582870a-37ee-4ea2-aa98-908b0cea2993" />


This is the backend infrastructure for an Italian grammar quiz application.

It is built entirely on AWS using Lambda, API Gateway, DynamoDB, and OpenAI.



It provides 2 endpoints:

- GET  /quiz/{level}           → Fetches questions for a given level

- POST /quiz/{level}/submit   → Grades answers and returns feedback using OpenAI (for incorrect answers only)



──────────────────────────────────────────────────────



📦 FEATURES



✅ Fully serverless (no servers to manage)  

🧠 OpenAI-powered grammar feedback (for mistakes)  

🛠️ Deployed using Terraform  

📈 Fast, scalable, stateless backend  



──────────────────────────────────────────────────────



```plaintext

italian-quiz-backend/

│

├── terraform/

│   ├── main.tf

│   ├── terraform.tfvars

│   └── lambda/

│       ├── get_questions_by_level.zip

│       ├── submit_quiz_answers.zip

│       └── layers/

│           └── openai_layer.zip

│

├── lambda_source/

│   ├── get_questions_by_level.py

│   ├── submit_quiz_answers.py

│   ├── fill_database.py

│   └── quiz_questions.txt        ← used by fill_database.py

│

├── .env.example

└── README.md





````



──────────────────────────────────────────────────────



⚙️ SETUP & DEPLOYMENT



1. 📝 Fill in terraform.tfvars
terraform.tfvars


aws_access_key   = "YOUR_AWS_ACCESS_KEY"

aws_secret_key   = "YOUR_AWS_SECRET_KEY"

openai_api_key   = "YOUR_OPENAI_API_KEY"


--------------------------
2. 📦 Zip the Lambda Code

From the lambda_source folder:



    zip ../terraform/lambda/get_questions_by_level.zip get_questions_by_level.py

    zip ../terraform/lambda/submit_quiz_answers.zip submit_quiz_answers.py



To create the Lambda Layer with dependencies:



    mkdir python

    pip install openai==0.28.1 tiktoken --target python

    zip -r openai_layer.zip python

    mv openai_layer.zip ../terraform/lambda/layers/



✔️ NOTE:

After testing, `openai==0.28.1` works best for AWS Lambda compatibility (tested and confirmed).


----------------------
3. 🚀 Deploy Terraform

    cd terraform

    terraform init

    terraform apply -var-file=terraform.tfvars


This will provision:

- API Gateway (2 routes)

- 2 Lambda functions

- 1 DynamoDB table

- IAM roles

- Lambda Layer with OpenAI deps


--------------------------------------
4. 🗃️ Populate DynamoDB with Questions


First, configure AWS CLI if you haven’t already:


    aws configure



It will prompt:



    AWS Access Key ID [None]: YOUR_KEY

    AWS Secret Access Key [None]: YOUR_SECRET

    Default region name [None]: eu-central-1

    Default output format [None]: json



Then run:



    python lambda_source/fill_database.py



The script reads from:

    lambda_source/quiz_questions.txt


-----------------------------
File format (pipe-separated):



<level>|<question>|<choice_1>|<choice_2>|<choice_3>|<choice_4>|<correct_choice_number>



Example:

1|Quale è la forma corretta del verbo "essere"?|sono|sei|è|siamo|3



──────────────────────────────────────────────────────



🌐 API ENDPOINTS


-----------------
GET /quiz/{level}



Returns a JSON list of quiz questions for the specified level.

--------------------------

POST /quiz/{level}/submit



Accepts user answers and returns:

- ✅ Score

- ❌ Explanations (only for incorrect answers)


--------------------
Sample JSON request:



{

  "answers": [

    { "question_id": "lvl1-q001", "answer": 2 },

    { "question_id": "lvl1-q002", "answer": 4 }

  ]

}



──────────────────────────────────────────────────────

🧪 TESTING THE BACKEND



Use Postman or curl:



    curl -X POST https://your-api-url/quiz/1/submit \

      -H "Content-Type: application/json" \

      -d '{"answers":[{"question_id":"lvl1-q001","answer":2}]}'


<img width="1655" height="875" alt="GET" src="https://github.com/user-attachments/assets/50451902-e4f2-4c9f-b121-03696030e527" />

<img width="1659" height="889" alt="POST" src="https://github.com/user-attachments/assets/bc4f7b90-1880-401f-a581-5308933b1e82" />


