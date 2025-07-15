terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region     = "eu-central-1"
  access_key = var.aws_access_key
  secret_key = var.aws_secret_key
}

variable "aws_access_key" {
  description = "AWS Access Key"
  type        = string
  sensitive   = true
}

variable "aws_secret_key" {
  description = "AWS Secret Key"
  type        = string
  sensitive   = true
}

variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
}

# DynamoDB Table
resource "aws_dynamodb_table" "quiz_questions" {
  name         = "ItalianQuizQuestions"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "level"
  range_key    = "question_id"

  attribute {
    name = "level"
    type = "N"
  }

  attribute {
    name = "question_id"
    type = "S"
  }
}

# IAM Role for Lambda
resource "aws_iam_role" "lambda_exec" {
  name = "lambda_exec_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = {
        Service = "lambda.amazonaws.com"
      },
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_policy_attachment" "lambda_dynamodb_policy" {
  name       = "lambda-dynamodb-attach"
  roles      = [aws_iam_role.lambda_exec.name]
  policy_arn = "arn:aws:iam::aws:policy/AmazonDynamoDBReadOnlyAccess"
}

resource "aws_iam_policy_attachment" "lambda_basic_execution" {
  name       = "lambda-basic-execution"
  roles      = [aws_iam_role.lambda_exec.name]
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Lambda Layer (OpenAI dependencies)
resource "aws_lambda_layer_version" "openai_layer" {
  layer_name          = "openai-layer"
  compatible_runtimes = ["python3.12"]
  filename            = "lambda/layers/openai_layer.zip"
  source_code_hash    = filebase64sha256("lambda/layers/openai_layer.zip")
}

# Lambda: get_questions
resource "aws_lambda_function" "get_questions_by_level" {
  function_name = "get_questions_by_level"
  handler       = "get_questions_by_level.lambda_handler"
  runtime       = "python3.12"
  role          = aws_iam_role.lambda_exec.arn
  filename      = "lambda/get_questions_by_level.zip"
  source_code_hash = filebase64sha256("lambda/get_questions_by_level.zip")

  environment {
    variables = {
      DDB_TABLE = aws_dynamodb_table.quiz_questions.name
    }
  }
}

# Lambda: submit_answers (with OpenAI)
resource "aws_lambda_function" "submit_quiz_answers" {
  function_name = "submit_quiz_answers"
  handler       = "submit_quiz_answers.lambda_handler"
  runtime       = "python3.12"
  role          = aws_iam_role.lambda_exec.arn
  filename      = "lambda/submit_quiz_answers.zip"
  source_code_hash = filebase64sha256("lambda/submit_quiz_answers.zip")

  environment {
    variables = {
      DDB_TABLE      = aws_dynamodb_table.quiz_questions.name
      OPENAI_API_KEY = var.openai_api_key
    }
  }

  layers = [aws_lambda_layer_version.openai_layer.arn]
}

# API Gateway
resource "aws_apigatewayv2_api" "quiz_api" {
  name          = "quiz_api"
  protocol_type = "HTTP"
}

# Integrations
resource "aws_apigatewayv2_integration" "get_questions_integration" {
  api_id             = aws_apigatewayv2_api.quiz_api.id
  integration_type   = "AWS_PROXY"
  integration_uri    = aws_lambda_function.get_questions_by_level.invoke_arn
  integration_method = "POST"
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "submit_answers_integration" {
  api_id             = aws_apigatewayv2_api.quiz_api.id
  integration_type   = "AWS_PROXY"
  integration_uri    = aws_lambda_function.submit_quiz_answers.invoke_arn
  integration_method = "POST"
  payload_format_version = "2.0"
}

# Routes
resource "aws_apigatewayv2_route" "get_questions_route" {
  api_id    = aws_apigatewayv2_api.quiz_api.id
  route_key = "GET /quiz/{level}"
  target    = "integrations/${aws_apigatewayv2_integration.get_questions_integration.id}"
}

resource "aws_apigatewayv2_route" "submit_answers_route" {
  api_id    = aws_apigatewayv2_api.quiz_api.id
  route_key = "POST /quiz/{level}/submit"
  target    = "integrations/${aws_apigatewayv2_integration.submit_answers_integration.id}"
}

# Lambda Permissions
resource "aws_lambda_permission" "allow_api_gateway_get_questions" {
  statement_id  = "AllowAPIGatewayInvokeGetQuestions"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_questions_by_level.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.quiz_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "allow_api_gateway_submit_answers" {
  statement_id  = "AllowAPIGatewayInvokeSubmitAnswers"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.submit_quiz_answers.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.quiz_api.execution_arn}/*/*"
}

# Stage
resource "aws_apigatewayv2_stage" "dev" {
  api_id      = aws_apigatewayv2_api.quiz_api.id
  name        = "dev"
  auto_deploy = true

  depends_on = [
    aws_apigatewayv2_route.get_questions_route,
    aws_apigatewayv2_route.submit_answers_route
  ]
}

# Outputs
output "quiz_api_url" {
  description = "Base URL for the quiz API"
  value       = "${aws_apigatewayv2_api.quiz_api.api_endpoint}/${aws_apigatewayv2_stage.dev.name}"
}

output "dynamodb_table_name" {
  value = aws_dynamodb_table.quiz_questions.name
}

output "lambda_get_questions_function_name" {
  value = aws_lambda_function.get_questions_by_level.function_name
}

output "lambda_submit_answers_function_name" {
  value = aws_lambda_function.submit_quiz_answers.function_name
}

output "api_gateway_id" {
  value = aws_apigatewayv2_api.quiz_api.id
}

output "api_gateway_stage_name" {
  value = aws_apigatewayv2_stage.dev.name
}

output "lambda_layer_arn" {
  value = aws_lambda_layer_version.openai_layer.arn
}
