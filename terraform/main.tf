terraform {
  required_version = ">= 1.7.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
  backend "s3" {
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project   = "ShopSecure"
      ManagedBy = "Terraform"
      Env       = var.environment
    }
  }
}

variable "aws_region"  { default = "ap-south-1" }
variable "environment" { type    = string }

# IAM: one role per Lambda (least privilege)
resource "aws_iam_role" "auth_role" {
  name = "shopsecure-${var.environment}-auth-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role" "products_role" {
  name = "shopsecure-${var.environment}-products-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role" "orders_role" {
  name = "shopsecure-${var.environment}-orders-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "auth_logs" {
  role       = aws_iam_role.auth_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}
resource "aws_iam_role_policy_attachment" "products_logs" {
  role       = aws_iam_role.products_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}
resource "aws_iam_role_policy_attachment" "orders_logs" {
  role       = aws_iam_role.orders_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Only auth Lambda can read JWT secret
resource "aws_iam_role_policy" "auth_secrets_policy" {
  name   = "read-jwt-secret"
  role   = aws_iam_role.auth_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["secretsmanager:GetSecretValue"]
      Resource = aws_secretsmanager_secret.jwt_secret.arn
    }]
  })
}

# Secrets Manager
resource "aws_secretsmanager_secret" "jwt_secret" {
  name                    = "shopsecure/${var.environment}/jwt-secret"
  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "jwt_value" {
  secret_id     = aws_secretsmanager_secret.jwt_secret.id
  secret_string = "REPLACE-WITH-LONG-RANDOM-STRING"
  lifecycle { ignore_changes = [secret_string] }
}

# Lambda Functions
resource "aws_lambda_function" "auth_lambda" {
  function_name    = "shopsecure-${var.environment}-auth-service"
  role             = aws_iam_role.auth_role.arn
  handler          = "app.lambda_handler"
  runtime          = "python3.11"
  timeout          = 30
  memory_size      = 256
  filename         = "../dist/auth-service.zip"
  source_code_hash = filebase64sha256("../dist/auth-service.zip")
  environment { variables = { ENVIRONMENT = var.environment } }
  tracing_config { mode = "Active" }
}

resource "aws_lambda_function" "products_lambda" {
  function_name    = "shopsecure-${var.environment}-product-service"
  role             = aws_iam_role.products_role.arn
  handler          = "app.lambda_handler"
  runtime          = "python3.11"
  timeout          = 30
  memory_size      = 256
  filename         = "../dist/product-service.zip"
  source_code_hash = filebase64sha256("../dist/product-service.zip")
  environment { variables = { ENVIRONMENT = var.environment } }
  tracing_config { mode = "Active" }
}

resource "aws_lambda_function" "orders_lambda" {
  function_name    = "shopsecure-${var.environment}-order-service"
  role             = aws_iam_role.orders_role.arn
  handler          = "app.lambda_handler"
  runtime          = "python3.11"
  timeout          = 60
  memory_size      = 256
  filename         = "../dist/order-service.zip"
  source_code_hash = filebase64sha256("../dist/order-service.zip")
  environment { variables = { ENVIRONMENT = var.environment } }
  tracing_config { mode = "Active" }
}

# API Gateway
resource "aws_api_gateway_rest_api" "main_api" {
  name = "shopsecure-${var.environment}"
  endpoint_configuration { types = ["REGIONAL"] }
}

resource "aws_lambda_permission" "auth_apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.auth_lambda.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main_api.execution_arn}/*/*"
}
resource "aws_lambda_permission" "products_apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.products_lambda.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main_api.execution_arn}/*/*"
}
resource "aws_lambda_permission" "orders_apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.orders_lambda.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main_api.execution_arn}/*/*"
}

# Security Monitoring

resource "aws_cloudwatch_log_group" "auth_logs" {
  name              = "/aws/lambda/shopsecure-${var.environment}-auth-service"
  retention_in_days = 30
}
resource "aws_cloudwatch_log_group" "products_logs" {
  name              = "/aws/lambda/shopsecure-${var.environment}-product-service"
  retention_in_days = 30
}
resource "aws_cloudwatch_log_group" "orders_logs" {
  name              = "/aws/lambda/shopsecure-${var.environment}-order-service"
  retention_in_days = 30
}

output "api_gateway_id" { value = aws_api_gateway_rest_api.main_api.id }
