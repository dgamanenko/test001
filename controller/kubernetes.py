from kubernetes import client, config
import logging

config.load_incluster_config()
extensions_v1_beta1 = client.ExtensionsV1beta1Api()
custom_api = client.CustomObjectsApi()

def create_custom_resource_definition():
    """
    Create the LambdaCanary custom resource definition.
    """
    crd = {
        "apiVersion": "apiextensions.k8s.io/v1beta1",
        "kind": "CustomResourceDefinition",
        "metadata": {
            "name": "lambdacanaries.awesomeapp.com"
        },
        "spec": {
            "group": "awesomeapp.com",
            "version": "v1",
            "names": {
                "plural": "lambdacanaries",
                "singular": "lambdacanary",
                "kind": "LambdaCanary",
                "shortNames": [
                    "canary"
                ]
            },
            "scope": "Namespaced",
            "subresources": {
                "status": {}
            },
            "validation": {
                "openAPIV3Schema": {
                    "properties": {
                        "functionName": {
                            "type": "string"
                        },
                        "newVersion": {
                            "type": "string"
                        },
                        "oldVersion": {
                            "type": "string"
                        },
                        "policy": {
                            "type": "object"
                        }
                    },
                    "required": [
                        "functionName",
                        "newVersion",
                        "oldVersion",
                        "policy"
                    ]
                }
            }
        }
    }

    try:
        custom_api.create_custom_resource_definition(crd)
        logging.info("LambdaCanary custom resource definition created.")
    except client.rest.ApiException as e:
        if e.status != 409:
            raise e
        logging.info("LambdaCanary custom resource definition already exists.")

def create_service_account(namespace):
    """
    Create the service account for the controller.
    """
    body = {
        "metadata": {
            "name": "lambda-canary-controller",
            "namespace": namespace
        }
    }

    try:
        api = client.CoreV1Api()
        api.create_namespaced_service_account(namespace, body)
        logging.info("Service account created.")
    except client.rest.ApiException as e:
        if e.status != 409:
            raise e
        logging.info("Service account already exists.")

def create_cluster_role(namespace):
    """
    Create the cluster role for the controller.
    """
    rules = [
        {
            "apiGroups": ["awesomeapp.com"],
            "resources": ["lambdacanaries"],
            "verbs": ["get", "list", "watch", "create", "update", "delete"]
        },
        {
            "apiGroups": [""],
            "resources": ["pods", "services"],
            "verbs": ["get", "list", "watch", "create", "update", "delete"]
        }
    ]

    body = {
        "apiVersion": "rbac.authorization.k8s.io/v1",
        "kind": "ClusterRole",
        "metadata": {
            "name": "lambda-canary-controller"
        },
        "rules": rules
    }

    try:
        api = client.RbacAuthorizationV1Api()
        api.create_cluster_role(body)
        logging.info("Cluster role created.")
    except client.rest.ApiException as e:
        if e.status != 409:
            raise e
        logging.info("Cluster role already exists.")

    def create_cluster_role_binding(namespace):
        """
        Create the cluster role binding for the service account.
        """
        body = {
            "apiVersion": "rbac.authorization.k8s.io/v1",
            "kind": "ClusterRoleBinding",
            "metadata": {
                "name": "lambda-canary-controller"
            },
            "roleRef": {
                "apiGroup": "rbac.authorization.k8s.io",
                "kind": "ClusterRole",
                "name": "lambda-canary-controller"
            },
            "subjects": [
                {
                    "kind": "ServiceAccount",
                    "name": "lambda-canary-controller",
                    "namespace": namespace
                }
            ]
        }

        try:
            api = client.RbacAuthorizationV1Api()
            api.create_cluster_role_binding(body)
            logging.info("Cluster role binding created.")
        except client.rest.ApiException as e:
            if e.status != 409:
                raise e
            logging.info("Cluster role binding already exists.")

    def create_deployment(namespace, image_tag):
        """
        Create the deployment for the controller.
        """
        deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": "lambda-canary-controller",
                "namespace": namespace,
                "labels": {
                    "app": "lambda-canary-controller"
                }
            },
            "spec": {
                "replicas": 1,
                "selector": {
                    "matchLabels": {
                        "app": "lambda-canary-controller"
                    }
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "app": "lambda-canary-controller"
                        }
                    },
                    "spec": {
                        "serviceAccountName": "lambda-canary-controller",
                        "containers": [
                            {
                                "name": "lambda-canary-controller",
                                "image": f"my-registry.com/lambda-canary-controller:{image_tag}",
                                "env": [
                                    {
                                        "name": "NAMESPACE",
                                        "valueFrom": {
                                            "fieldRef": {
                                                "fieldPath": "metadata.namespace"
                                            }
                                        }
                                    },
                                    {
                                        "name": "JWT_SECRET",
                                        "valueFrom": {
                                            "secretKeyRef": {
                                                "name": "jwt-secret",
                                                "key": "jwt-secret"
                                            }
                                        }
                                    }
                                ],
                                "resources": {
                                    "limits": {
                                        "cpu": "0.5",
                                        "memory": "512Mi"
                                    },
                                    "requests": {
                                        "cpu": "0.1",
                                        "memory": "64Mi"
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        }

        try:
            api = client.AppsV1Api()
            api.create_namespaced_deployment(namespace, deployment)
            logging.info("Deployment created.")
        except client.rest.ApiException as e:
            if e.status != 409:
                raise e
            logging.info("Deployment already exists.")