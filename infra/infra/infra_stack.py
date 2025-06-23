from aws_cdk import (
    Stack,
    Size,
    CfnOutput,
    Duration,
    RemovalPolicy,
    aws_lex as lex,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_apigateway as apigateway,
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
)
from constructs import Construct
import os


def create_message(message):
    """
    Creates a message group property based on AWS LEX

    Arguments:-
        message: str - message to be displayed
    Returns:-
        propery
    """
    return lex.CfnBot.MessageGroupProperty(
        message=lex.CfnBot.MessageProperty(
            plain_text_message=lex.CfnBot.PlainTextMessageProperty(
                value=message)))


class InfraChatbotStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ## Create an IAM role for the Lex bot
        role_lex = iam.Role(
            self, "RoleLexBot",
            assumed_by=iam.ServicePrincipal("lexv2.amazonaws.com")
        )
        role_lex.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonLexFullAccess")
        )

        role_lambda = iam.Role(
            self, "RoleLambda",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com")
        )
        role_lambda.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
        )

        ## Create Lex Lambda role for lex inference
        role_lex_lambda = iam.Role(
            self, "LexLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonLexFullAccess")
            ]
        )

        # Create fulfilment Lambda function
        lambda_fulfillment = lambda_.Function(
            self, "LambdaFulfillment",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="lambda_function.handler",
            code=lambda_.Code.from_asset(
                path=os.path.join("..", "backend", "lambda_fulfillment"),
                bundling={
                    "image": lambda_.Runtime.PYTHON_3_12.bundling_image,
                    "command": [
                        "bash", "-c",
                        "cp lambda_function.py /asset-output"
                    ]
                }
            ),
            role=role_lambda,
            memory_size=1024,
            ephemeral_storage_size=Size.mebibytes(1024)
        )

        # Grant Lex permission to invoke FulfillmentLambda
        lambda_fulfillment.add_permission(
            "LexInvokePermission",
            principal=iam.ServicePrincipal("lexv2.amazonaws.com"),
            source_arn=f"arn:aws:lex:{self.region}:{self.account}:bot-alias/*/*"
        )

        # Create Lex bot
        bot = lex.CfnBot(

            # Basic Configuration
            self, "MusicRecommender",
            name="MoodBasedMusicRecommender",
            data_privacy={"ChildDirected": False},
            idle_session_ttl_in_seconds=300,
            role_arn=role_lex.role_arn,
            auto_build_bot_locales=True,
            test_bot_alias_settings=lex.CfnBot.TestBotAliasSettingsProperty(
                bot_alias_locale_settings=[
                    lex.CfnBot.BotAliasLocaleSettingsItemProperty(
                        locale_id="en_US",
                        bot_alias_locale_setting=lex.CfnBot.BotAliasLocaleSettingsProperty(
                            enabled=True,
                            code_hook_specification=lex.CfnBot.CodeHookSpecificationProperty(
                                lambda_code_hook=lex.CfnBot.LambdaCodeHookProperty(
                                    lambda_arn=lambda_fulfillment.function_arn,
                                    code_hook_interface_version="1.0"
                                )
                            )
                        )
                    )
                ]
            ),
            bot_locales=[
                lex.CfnBot.BotLocaleProperty(
                    locale_id="en_US",
                    nlu_confidence_threshold=0.4,
                    voice_settings=lex.CfnBot.VoiceSettingsProperty(voice_id="Ivy"),
                    intents=[
                        # Define journey planning Intent
                        lex.CfnBot.IntentProperty(
                            name="GetMusicRecommendation",
                            sample_utterances=[
                                lex.CfnBot.SampleUtteranceProperty(utterance=utterance)
                                for utterance in [
                                    "music",
                                    "Suggest some music",
                                    "Recommend a song",
                                    "Recommend me some music",
                                    "I want to listen to music",
                                    "Suggest a song for me",
                                    "What should I listen to?",
                                    "I am in a {mood} mood",
                                    "Play some music for my {mood} mood",
                                    "I am feeling {mood} , what do you suggest?",
                                    "Suggest a song based on my {mood} mood",
                                    "I want to listen to {genre} music",
                                    "Recommend a {genre} song for me",
                                    "Suggest a {genre} song",
                                    "I am in a {mood} mood. Suggest me some {genre} music",
                                    "I am feeling {mood} and want to listen to {genre} music",
                                    "Feeling {mood} , what {genre} music do you suggest?",
                                ]
                            ],

                            # Define slots
                            slots=[
                                lex.CfnBot.SlotProperty(
                                    name="mood",
                                    slot_type_name="AMAZON.AlphaNumeric",
                                    value_elicitation_setting=lex.CfnBot.SlotValueElicitationSettingProperty(
                                        slot_constraint="Required",
                                        prompt_specification=lex.CfnBot.PromptSpecificationProperty(
                                            max_retries=2,
                                            message_groups_list=[create_message("What is your current mood?")]
                                        )
                                    )
                                ),
                                lex.CfnBot.SlotProperty(
                                    name="genre",
                                    slot_type_name="AMAZON.AlphaNumeric",
                                    value_elicitation_setting=lex.CfnBot.SlotValueElicitationSettingProperty(
                                        slot_constraint="Optional",
                                        prompt_specification=lex.CfnBot.PromptSpecificationProperty(
                                            max_retries=2,
                                            message_groups_list=[create_message("What genre do you want to listen?")]
                                        )
                                    )
                                )
                            ],

                            # Define slot priorities to enforce order
                            slot_priorities=[
                                lex.CfnBot.SlotPriorityProperty(
                                    priority=index,
                                    slot_name=slot_name
                                )
                                for index, slot_name in enumerate(["mood", "genre"])
                            ],

                            # Confirmation setting
                            intent_confirmation_setting=lex.CfnBot.IntentConfirmationSettingProperty(
                                prompt_specification=lex.CfnBot.PromptSpecificationProperty(
                                    max_retries=2,
                                    message_groups_list=[create_message("Shall i look for music based on your mood?")]
                                ),
                                declination_response=lex.CfnBot.ResponseSpecificationProperty(
                                    message_groups_list=[create_message("Okay, let me know if you need anything else.")],
                                )
                            ),

                            # Fulfillment setting
                            fulfillment_code_hook=lex.CfnBot.FulfillmentCodeHookSettingProperty(
                                enabled=True
                            ),

                            # Intent closing setting
                            intent_closing_setting=lex.CfnBot.IntentClosingSettingProperty(
                                closing_response=lex.CfnBot.ResponseSpecificationProperty(
                                    message_groups_list=[create_message("Do you need any more recommendations?")],
                                )
                            )
                        ),

                        # Define CancelIntent
                        lex.CfnBot.IntentProperty(
                            name="CancelIntent",  # The name must be "CancelIntent"
                            description="Allows the user to cancel the current conversation after response.",
                            parent_intent_signature="AMAZON.CancelIntent"
                        ),

                        # Define StopIntent
                        lex.CfnBot.IntentProperty(
                            name="StopIntent",  # The name must be "StopIntent"
                            description="Allows the user to stop the current conversation.",
                            parent_intent_signature="AMAZON.StopIntent"
                        ),

                        # Define StartOverIntent
                        lex.CfnBot.IntentProperty(
                            name="StartOverIntent",  # The name must be "StartOverIntent"
                            description="Allows the user to start the conversation over.",
                            parent_intent_signature="AMAZON.StartOverIntent"
                        ),

                        # Fallback Intent setting
                        lex.CfnBot.IntentProperty(
                            name="FallbackIntent",
                            description="Fallback intent to handle unrecognized utterances.",
                            parent_intent_signature="AMAZON.FallbackIntent",
                            # Fulfillment setting
                            fulfillment_code_hook=lex.CfnBot.FulfillmentCodeHookSettingProperty(
                                enabled=True
                            ),
                        )
                    ]
                )
            ]
        )

        # Create api Lambda function
        lambda_api = lambda_.Function(
            self, "LambdaApi",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="lambda_function.handler",
            code=lambda_.Code.from_asset(
                path=os.path.join("..", "backend", "lambda_api"),
                bundling={
                    "image": lambda_.Runtime.PYTHON_3_12.bundling_image,
                    "command": [
                        "bash", "-c",
                        "pip install -r requirements.txt -t /asset-output && cp lambda_function.py /asset-output"
                    ]
                }
            ),
            role=role_lex_lambda,
            memory_size=1024,
            ephemeral_storage_size=Size.mebibytes(1024),
            environment={
                "LEX_BOT_ID": bot.attr_id,
                "LEX_BOT_ALIAS_ID": "TSTALIASID",
                "LEX_LOCALE_ID": "en_US"
            }
        )

        # Grant Lex permission to invoke Lambda
        lambda_api.add_permission(
            "LexInvokePermission",
            principal=iam.ServicePrincipal("lexv2.amazonaws.com"),
            source_arn=f"arn:aws:lex:{self.region}:{self.account}:bot-alias/*/*"
        )

        # API Gateway REST API (Option 1A)
        api = apigateway.LambdaRestApi(
            self, "FastAPIGateway",
            handler=lambda_api,
            proxy=True,  # Proxy all requests to Lambda
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=["*"]
            )
        )

        # S3 Bucket for React App
        frontend_bucket = s3.Bucket(
            self, "ChatbotFrontendBucket",
            # RemovalPolicy.DESTROY is for dev/testing, use RETAIN in production
            removal_policy=RemovalPolicy.DESTROY,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL
        )
        logging_bucket = s3.Bucket(
            self, "CloudFrontLoggingBucket",
            object_ownership=s3.ObjectOwnership.OBJECT_WRITER,  # ✅ Enables ACLs
            removal_policy=RemovalPolicy.DESTROY  # Optional, for cleanup in dev
        )

        # CloudFront Origin Access Identity (OAI) for S3
        oai = cloudfront.OriginAccessIdentity(
            self, "ChatbotFrontendOAI",
            comment="OAI for CloudFront to access S3 bucket"
        )

        # Grant OAI read access to the S3 bucket
        frontend_bucket.grant_read(oai)

        # CloudFront Distribution
        distribution = cloudfront.Distribution(
            self, "ChatbotCloudFrontDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(frontend_bucket, origin_access_identity=oai),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS
            ),
            default_root_object="index.html",
            error_responses=[
                cloudfront.ErrorResponse(
                    http_status=403,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.seconds(0)
                ),
                cloudfront.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.seconds(0)
                )
            ],
            log_bucket=logging_bucket
        )

        # Output the CloudFront URL
        CfnOutput(
            self,
            "CloudFrontUrl",
            value=f"https://{distribution.distribution_domain_name}",
            export_name="CloudFrontUrl"
        )

        # Save the API URL
        CfnOutput(
            self,
            "APIEndpoint",
            value=api.url,
            export_name="APIEndpoint"
        )

        # Save bot id
        CfnOutput(
            self,
            "LexBotId",
            value=bot.ref,  # this is the bot ID
            export_name="LexBotId"
        )
    
        # Output S3 bucket name
        CfnOutput(
            self,
            "WebsiteBucketName",
            value=frontend_bucket.bucket_name,
            export_name="WebsiteBucketName",
            description="S3 bucket name for the static website"
        )

        # Output CloudFront distribution URL
        CfnOutput(
            self,
            "WebsiteURL",
            value=f"https://{distribution.distribution_domain_name}",
            export_name="WebsiteURL",
            description="CloudFront distribution URL for the chatbot website"
        )

        # Output CloudFront distribution ID
        CfnOutput(
            self,
            "DistributionId",
            value=distribution.distribution_id,
            export_name="DistributionId",
            description="CloudFront distribution ID for cache invalidation"
        )