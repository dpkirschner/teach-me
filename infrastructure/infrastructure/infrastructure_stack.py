import json
from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_logs as logs,
    Duration,
    CfnOutput,
)
from constructs import Construct

class InfrastructureStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        with open("config.json", "r") as f:
            config = json.load(f)

        lambda_conf = config["lambda_config"]
        api_conf = config["api_gateway_config"]

        log_group = logs.LogGroup(
            self,
            "FastAPILambdaLogGroup",
            retention=logs.RetentionDays.ONE_WEEK
        )

        fastapi_lambda = _lambda.Function(
            self,
            "TeachMeLambdaHandler",
            runtime=_lambda.Runtime.PYTHON_3_11,
            code=_lambda.Code.from_asset("../src/lambda"),
            handler="index.handler",
            memory_size=lambda_conf["memory_size"],
            timeout=Duration.seconds(lambda_conf["timeout"]),
            environment=lambda_conf["environment"],
            log_group=log_group
        )

        api = apigw.LambdaRestApi(
            self,
            "TeachMeAPIEndpoint",
            handler=fastapi_lambda,
            proxy=True,
            deploy_options=apigw.StageOptions(
                stage_name=api_conf["stage"],
                throttling_rate_limit=api_conf["throttle"]["rate_limit"],
                throttling_burst_limit=api_conf["throttle"]["burst_limit"]
            )
        )

        CfnOutput(self, "ApiEndpointUrl",
            value=api.url,
            description="The URL of the API Gateway endpoint"
        )