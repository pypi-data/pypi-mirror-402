"""
Execution Handler Abstract Base Class

This module provides the ExecutionHandler abstract base class that defines
the interface for execution handlers used by CWL runners. Execution handlers
provide hooks for customizing execution behavior.
"""

from abc import ABC, abstractmethod


class ExecutionHandler(ABC):
    """
    Abstract base class for execution handlers.

    Execution handlers provide hooks that allow customization of CWL workflow
    execution behavior at various stages. Subclasses must implement all abstract
    methods to provide concrete execution logic.
    """

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.job_id = getattr(self, 'job_id', None)
        self.outputs = getattr(self, 'outputs', {})
        self.results = getattr(self, 'results', None)

    def set_job_id(self, job_id):
        """Set the job ID for the execution."""
        self.job_id = job_id

    @abstractmethod
    def pre_execution_hook(self):
        """
        Hook called before workflow execution starts.

        Use this hook to perform setup operations, validate environment,
        configure resources, or prepare the execution context.
        """
        pass

    @abstractmethod
    def post_execution_hook(self, log, output, usage_report, tool_logs):
        """
        Hook called after workflow execution completes.

        Args:
            log: Execution log information
            output: Workflow output data
            usage_report: Resource usage information
            tool_logs: Logs from individual tools in the workflow

        Use this hook for cleanup, result validation, or post-processing.
        """
        pass

    @abstractmethod
    def get_secrets(self):
        """
        Get secrets required for workflow execution.

        Returns:
            dict: Dictionary of secret names to secret values

        Use this to provide credentials, API keys, or other sensitive
        configuration data needed during execution.
        """
        pass

    @abstractmethod
    def get_pod_env_vars(self):
        """
        Get environment variables for execution pods/containers.

        Returns:
            dict: Dictionary of environment variable names to values

        These environment variables will be set in the execution environment
        (e.g., Kubernetes pods, Docker containers).
        """
        pass

    @abstractmethod
    def get_pod_node_selector(self):
        """
        Get node selector for scheduling execution pods.

        Returns:
            dict: Dictionary of node selector labels

        Used in Kubernetes environments to control which nodes can run
        the execution pods. Return empty dict for no node selection.
        """
        pass

    @abstractmethod
    def handle_outputs(self, log, output, usage_report, tool_logs):
        """
        Handle workflow outputs.

        Args:
            log: Execution log information
            output: Workflow output data
            usage_report: Resource usage information
            tool_logs: Logs from individual tools

        Use this hook to process, validate, or transform workflow outputs
        before they are returned to the caller.
        """
        pass

    @abstractmethod
    def get_additional_parameters(self):
        """
        Get additional parameters for workflow execution.

        Returns:
            dict: Dictionary of parameter names to values

        These parameters will be merged with the workflow inputs and can
        be used to provide configuration or runtime parameters.
        """
        pass
