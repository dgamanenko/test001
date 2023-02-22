import boto3
import logging

from botocore.exceptions import ClientError


class LambdaClient:
    def __init__(self, region_name):
        self._client = boto3.client("lambda", region_name=region_name)

    def update_alias(self, function_name, function_version, alias_name):
        """
        Update an alias on a Lambda function with the specified version.
        """
        try:
            self._client.update_alias(
                FunctionName=function_name,
                Name=alias_name,
                FunctionVersion=function_version
            )
            logging.info(f"Alias '{alias_name}' on '{function_name}' updated to '{function_version}'.")
        except ClientError as e:
            logging.error(f"Could not update alias '{alias_name}' on '{function_name}': {e.response['Error']['Message']}.")
            raise e

    def create_canary_version(self, function_name, code_sha_256, execution_role_arn):
        """
        Create a new version of a Lambda function with the specified code SHA-256 hash.
        """
        try:
            response = self._client.create_canary_version(
                FunctionName=function_name,
                CodeSha256=code_sha_256,
                ExecutionRoleArn=execution_role_arn
            )
            version = response.get("Version")
            logging.info(f"Canary version '{version}' of '{function_name}' created.")
            return version
        except ClientError as e:
            logging.error(f"Could not create canary version of '{function_name}': {e.response['Error']['Message']}.")
            raise e

    def promote_canary_version(self, function_name, version, alias_name):
        """
        Promote a canary version of a Lambda function to production by updating an alias.
        """
        try:
            self.update_alias(function_name, version, alias_name)
            logging.info(f"Canary version '{version}' of '{function_name}' promoted to production.")
        except ClientError as e:
            logging.error(f"Could not promote canary version of '{function_name}': {e.response['Error']['Message']}.")
            raise e

    def delete_canary_version(self, function_name, version):
        """
        Delete a canary version of a Lambda function.
        """
        try:
            self._client.delete_function(
                FunctionName=function_name,
                Qualifier=version
            )
            logging.info(f"Canary version '{version}' of '{function_name}' deleted.")
        except ClientError as e:
            logging.error(f"Could not delete canary version '{version}' of '{function_name}': {e.response['Error']['Message']}.")
            raise e

    def get_function_code_sha_256(self, function_name, qualifier):
        """
        Get the SHA-256 hash of the code of a Lambda function.
        """
        try:
            response = self._client.get_function(
                FunctionName=function_name,
                Qualifier=qualifier
            )
            code_sha_256 = response.get("Configuration", {}).get("CodeSha256")
            if not code_sha_256:
                message = f"Code SHA-256 for '{function_name}:{qualifier}' not found."
                logging.error(message)
                raise ValueError(message)
            return code_sha_256
        except ClientError as e:
            logging.error(f"Could not get code SHA-256 for '{function_name}:{qualifier}': {e.response['Error']['Message']}.")
            raise e

    def create_health_check(self, function_name):
        """
        Create a health check for a Lambda function.
        """
        try:
            response = self._client.create_function_event_invoke_config(
                FunctionName=function_name,
                MaximumRetryAttempts=3,
                DestinationConfig={
                    "OnSuccess": {
                        "Destination": function_name
                    },
                    "OnFailure": {
                        "Destination": function_name
                    }
                }
            )
            logging.info(f"Health check for '{function_name}' created.")
            return response.get("FunctionEventInvokeConfig")
        except ClientError as e:
            logging.error(f"Could not create health check for '{function_name}': {e.response['Error']['Message']}.")
            raise e

    def delete_health_check(self, function_name):
        """
        Delete a health check for a Lambda function.
        """
        try:
            response = self._client.list_function_event_invoke_configs(FunctionName=function_name)
            if not response.get("FunctionEventInvokeConfigs"):
                logging.warning(f"No health check for '{function_name}' found.")
                return
            for config in response.get("FunctionEventInvokeConfigs"):
                self._client.delete_function_event_invoke_config(
                    FunctionName=function_name,
                    UUID=config.get("UUID")
                )
                logging.info(f"Health check for '{function_name}' deleted.")
        except ClientError as e:
            logging.error(f"Could not delete health check for '{function_name}': {e.response['Error']['Message']}.")
            raise e

    def invoke_lambda(self, function_name, payload):
        """
        Invoke a Lambda function with the specified payload.
        """
        try:
            response = self._client.invoke(
                FunctionName=function_name,
                Payload=payload
            )
            logging.info(f"Function '{function_name}' invoked.")
            return response["Payload"].read().decode("utf-8")
        except ClientError as e:
            logging.error(f"Could not invoke function '{function_name}': {e.response['Error']['Message']}.")
            raise e