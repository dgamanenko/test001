
import logging
import os
import time

from .lambda_client import LambdaClient
from .kubernetes_client import KubernetesClient
from .metrics import Metrics
from .policies import Policies

class Controller:
    def __init__(self, lambda_client, kubernetes_client, metrics, policies):
        self.lambda_client = lambda_client
        self.kubernetes_client = kubernetes_client
        self.metrics = metrics
        self.policies = policies

    def run(self):
        while True:
            for canary in self.kubernetes_client.get_canaries():
                self.rollout_canary(canary)
            time.sleep(30)

    def rollback_canary(self, function_name):
        canary = self.kubernetes_client.get_canary(function_name)

        if canary.status.phase == "ROLLED_BACK":
            logging.warning(f"{function_name}: Canary already rolled back...")
            return

        stable_version = self.lambda_client.get_stable_version(function_name)

        self.lambda_client.update_alias(
            function_name=function_name, alias="release", version=stable_version
        )

        self.kubernetes_client.update_canary_status(function_name, "ROLLED_BACK")
        logging.warning(f"{function_name}: Canary rolled back...")

    def update_canary_status(self, function_name, status):
        """
        Update the status of the canary deployment.
        """
        canary = self.kubernetes_client.get_canary(function_name)

        canary.status.phase = status

        self.kubernetes_client.update_canary(canary)

    def get_canary_status(self, function_name):
        """
        Get the current status of the canary deployment.
        """
        canary = self.kubernetes_client.get_canary(function_name)
        return canary.status.phase

    def get_canary_statuses(self):
        """
        Get the current status of all canary deployments.
        """
        canaries = self.kubernetes_client.get_canaries()
        return [{"name": c.spec.function_name, "status": c.status.phase} for c in canaries]

    def invoke_lambda(self, function_name, payload):
        """
        Invoke the specified AWS Lambda function with the given payload.
        """
        response = self.lambda_client.invoke(function_name, payload)
        return response["StatusCode"], response["Payload"].read().decode()

    def rollout_canary(self, canary):
        """
        Roll out the canary deployment.
        """
        function_name = canary.spec.function_name

        if canary.status.phase == "ROLLED_BACK":
            return

        if canary.status.phase == "RUNNING":
            self.promote_canary(canary)
            return

        stable_version = self.lambda_client.get_stable_version(function_name)

        if not stable_version:
            logging.warning(f"{function_name}: No stable version found...")
            return

        self.lambda_client.update_alias(
            function_name=function_name, alias="canary", version=canary.spec.version
        )

        self.kubernetes_client.update_canary_status(function_name, "PENDING")

        if not self.lambda_client.is_function_available(function_name, canary.spec.version):
            self.rollback_canary(function_name)
            return

        if self.policies.should_promote(function_name, canary.spec.version):
            self.promote_canary(canary)

    def promote_canary(self, canary):
        """
        Promote the canary deployment to stable.
        """
        function_name = canary.spec.function_name

        if canary.status.phase != "RUNNING":
            return

        self.lambda_client.update_alias(
            function_name=function_name, alias="release", version=canary.spec.version
        )

        self.kubernetes_client.update_canary_status(function_name, "PROMOTED")
        logging.warning(f"{function_name}: Canary promoted to stable...")

    def create_lambda_client(self):
        """
        Create a new `LambdaClient` instance.
        """
        return LambdaClient()

    def create_kubernetes_client(self):
        """
        Create a new `KubernetesClient` instance.
        """
        return KubernetesClient()

    def create_metrics(self):
        """
        Create a new `Metrics` instance.
        """
        return Metrics()

    def create_policies(self):
        """
        Create a new `Policies` instance.
        """
        return Policies()

    def get_canary_endpoint(self):
        """
        Get the endpoint for the canary deployment.
        """
        return os.environ.get("CANARY_ENDPOINT", "http://localhost:8080")

    def get_token_secret(self):
        """
        Get the token secret.
        """
        return os.environ.get("TOKEN_SECRET", "my-secret")

    def start(self):
        """
        Start the controller.
        """
        self.kubernetes_client.create_custom_resource_definition()
        self.kubernetes_client.create_cluster_role()
        self.kubernetes_client.create_cluster_role_binding(self.get_service_account_name())
        self.kubernetes_client.create_deployment(
            self.get_deployment_name(), self.get_service_account_name()
        )

        logging.warning("Controller started...")

    def get_deployment_name(self):
        """
        Get the name of the deployment.
        """
        return os.environ.get("DEPLOYMENT_NAME", "lambda-canary-controller")

    def get_service_account_name(self):
        """
        Get the name of the service account.
        """
        return os.environ.get("SERVICE_ACCOUNT_NAME", "lambda-canary-controller")
