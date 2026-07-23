resource "aws_cloudwatch_log_group" "access" {
  name              = "/aws/apigateway/${var.api_name}"
  retention_in_days = var.access_log_retention_days
  tags              = merge(var.tags, { Name = "${var.api_name}-access-logs" })
}

data "aws_iam_policy_document" "access_logs" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["apigateway.amazonaws.com"]
    }

    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]

    resources = ["${aws_cloudwatch_log_group.access.arn}:*"]
  }
}

resource "aws_cloudwatch_log_resource_policy" "access_logs" {
  policy_name     = "${var.api_name}-access-logs"
  policy_document = data.aws_iam_policy_document.access_logs.json
}

resource "aws_apigatewayv2_api" "this" {
  name          = var.api_name
  protocol_type = "HTTP"
  tags          = merge(var.tags, { Name = var.api_name })

  cors_configuration {
    allow_headers = ["authorization", "content-type"]
    allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_origins = var.allowed_origins
    max_age       = 3600
  }
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = aws_apigatewayv2_api.this.id
  integration_type       = "AWS_PROXY"
  integration_uri        = var.lambda_invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_authorizer" "clerk" {
  api_id           = aws_apigatewayv2_api.this.id
  name             = "${var.api_name}-clerk"
  authorizer_type  = "JWT"
  identity_sources = ["$request.header.Authorization"]

  jwt_configuration {
    issuer   = var.clerk_jwt_issuer
    audience = [var.clerk_jwt_audience]
  }
}

resource "aws_apigatewayv2_route" "readings" {
  api_id             = aws_apigatewayv2_api.this.id
  route_key          = "ANY /api/v1/readings"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.clerk.id
  target             = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_route" "reading_proxy" {
  api_id             = aws_apigatewayv2_api.this.id
  route_key          = "ANY /api/v1/readings/{proxy+}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.clerk.id
  target             = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_route" "jobs" {
  api_id             = aws_apigatewayv2_api.this.id
  route_key          = "GET /api/v1/jobs"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.clerk.id
  target             = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_route" "settings_get" {
  api_id             = aws_apigatewayv2_api.this.id
  route_key          = "GET /api/v1/settings"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.clerk.id
  target             = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_route" "settings_put" {
  api_id             = aws_apigatewayv2_api.this.id
  route_key          = "PUT /api/v1/settings"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.clerk.id
  target             = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_route" "tts_options" {
  api_id             = aws_apigatewayv2_api.this.id
  route_key          = "GET /api/v1/tts-options"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.clerk.id
  target             = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_route" "public_health" {
  api_id    = aws_apigatewayv2_api.this.id
  route_key = "GET /api/v1/health"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_route" "public_docs" {
  api_id    = aws_apigatewayv2_api.this.id
  route_key = "GET /docs"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_route" "public_redoc" {
  api_id    = aws_apigatewayv2_api.this.id
  route_key = "GET /redoc"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_route" "public_openapi" {
  api_id    = aws_apigatewayv2_api.this.id
  route_key = "GET /openapi.json"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.this.id
  name        = "$default"
  auto_deploy = true
  tags        = merge(var.tags, { Name = "${var.api_name}-default-stage" })

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.access.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      routeKey       = "$context.routeKey"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
      integrationErr = "$context.integrationErrorMessage"
    })
  }

  depends_on = [aws_cloudwatch_log_resource_policy.access_logs]
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowExecutionFromApiGateway"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.this.execution_arn}/*/*"
}
