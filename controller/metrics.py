import boto3
import logging

from botocore.exceptions import ClientError


class CloudWatchClient:
    def __init__(self, region_name):
        self._client = boto3.client("cloudwatch", region_name=region_name)

    def get_metric_statistics(self, function_name, start_time, end_time):
        """
        Get the average and maximum invocation latency of a Lambda function for a specified time period.
        """
        try:
            response = self._client.get_metric_statistics(
                Namespace="AWS/Lambda",
                MetricName="Duration",
                Dimensions=[
                    {
                        "Name": "FunctionName",
                        "Value": function_name
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=60,
                Statistics=[
                    "Average",
                    "Maximum"
                ]
            )
            datapoints = response.get("Datapoints", [])
            if not datapoints:
                logging.warning(f"No metric statistics found for '{function_name}'.")
                return None
            latest_datapoint = max(datapoints, key=lambda dp: dp["Timestamp"])
            return {
                "average": latest_datapoint.get("Average"),
                "maximum": latest_datapoint.get("Maximum")
            }
        except ClientError as e:
            logging.error(f"Could not get metric statistics for '{function_name}': {e.response['Error']['Message']}.")
            raise e