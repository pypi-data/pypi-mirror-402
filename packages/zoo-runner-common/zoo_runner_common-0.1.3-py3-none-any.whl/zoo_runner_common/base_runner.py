import logging
import os
import sys
import traceback
import types
from abc import ABC, abstractmethod

# Shared ZooStub import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

try:
    import zoo
except ImportError:
    from zoostub import ZooStub

    zoo = ZooStub()

from zoo_runner_common.zoo_conf import CWLWorkflow, ZooConf, ZooInputs, ZooOutputs

logger = logging.getLogger()


class BaseRunner(ABC):
    """
    Base class for CWL workflow runners.
    Provides common functionality and defines the interface for specific runners.
    """

    def __init__(self, cwl, inputs, conf, outputs, execution_handler=None):
        """
        Initialize the base runner.

        :param cwl: CWL workflow definition (path to file or parsed CWL)
        :param inputs: ZOO inputs dictionary
        :param conf: ZOO configuration dictionary
        :param outputs: ZOO outputs dictionary
        :param execution_handler: Optional ExecutionHandler instance for hooks
        """
        self.cwl = cwl
        self.execution_handler = execution_handler or self._create_default_handler()

        # Create typed wrapper objects from ZOO dictionaries
        self.conf = ZooConf(conf)
        self.inputs = ZooInputs(inputs)
        self.outputs = ZooOutputs(outputs)

        # Parse CWL workflow
        self.workflow = CWLWorkflow(self.cwl, self.conf.workflow_id)

        # Legacy namespace for backward compatibility
        self.zoo_conf = types.SimpleNamespace(conf=conf)

        # Runner-specific state
        self.namespace_name = None
        self.execution = None

    def _create_default_handler(self):
        """Create a default handler if none provided."""

        class DefaultHandler:
            def pre_execution_hook(self):
                pass

            def post_execution_hook(self, *args, **kwargs):
                pass

            def get_secrets(self):
                return None

            def get_additional_parameters(self):
                return {}

            def get_pod_env_vars(self):
                return None

            def get_pod_node_selector(self):
                return None

            def handle_outputs(self, *args, **kwargs):
                pass

            def set_job_id(self, job_id):
                pass

            def get_namespace(self):
                """Get namespace for Calrissian execution."""
                return None

            def get_service_account(self):
                """Get service account for Calrissian execution."""
                return None

        return DefaultHandler()

    def update_status(self, progress: int, message: str = ""):
        """
        Update execution status in ZOO.

        Args:
            progress: Progress percentage (0-100)
            message: Status message to display
        """
        if hasattr(self.conf, 'conf') and "lenv" in self.conf.conf:
            self.conf.conf["lenv"]["message"] = message
            zoo.update_status(self.conf.conf, progress)
        else:
            logger.warning("Cannot update status: conf structure not available")

    def get_namespace_name(self):
        """
        Generate a namespace name for Kubernetes resources.

        Returns:
            str: Namespace name in format {workflow_id}-{unique_id}
        """
        if self.namespace_name is None:
            import uuid
            unique_id = str(uuid.uuid4())[:8]
            self.namespace_name = f"{self.get_workflow_id()}-{unique_id}".lower()

        return self.namespace_name

    def log_output(self, output):
        """Log output information."""
        logger.info("[BaseRunner] Output: %s", output)

    def validate_inputs(self):
        """Validate input parameters."""
        logger.info("[BaseRunner] Validating inputs...")
        return True

    def prepare(self):
        """
        Shared pre-execution logic.
        Calls execution handler hooks and prepares processing parameters.
        """
        logger.info("execution started")
        self.update_status(progress=2, message="starting execution")

        # Call pre-execution hook
        if self.execution_handler and hasattr(
            self.execution_handler, "pre_execution_hook"
        ):
            try:
                self.execution_handler.pre_execution_hook()
            except Exception as e:
                logger.error(f"Error in pre_execution_hook: {e}")
                logger.error(traceback.format_exc())
                raise

        logger.info("wrap CWL workflow with stage-in/out steps")

        processing_parameters = {
            **self.get_processing_parameters(),
            **(
                self.execution_handler.get_additional_parameters()
                if self.execution_handler
                else {}
            ),
        }

        return types.SimpleNamespace(cwl=self.wrap(), params=processing_parameters)

    def finalize(self, log, output, usage_report, tool_logs):
        """
        Finalization logic after execution.
        Calls execution handler post-execution and output handling hooks.
        """
        logger.info("Finalization started")

        # Call post-execution hook
        if self.execution_handler and hasattr(
            self.execution_handler, "post_execution_hook"
        ):
            try:
                self.execution_handler.post_execution_hook(
                    log, output, usage_report, tool_logs
                )
            except Exception as e:
                logger.error(f"Error in post_execution_hook: {e}")
                logger.error(traceback.format_exc())
                raise

        # Call handle_outputs hook
        if self.execution_handler and hasattr(self.execution_handler, "handle_outputs"):
            try:
                self.execution_handler.handle_outputs(
                    log, output, usage_report, tool_logs
                )
            except Exception as e:
                logger.error(f"Error in handle_outputs: {e}")
                logger.error(traceback.format_exc())
                raise

    def get_workflow_id(self):
        """
        Get the workflow identifier from configuration.

        Returns:
            str: The workflow identifier
        """
        return self.conf.workflow_id

    def get_workflow_inputs(self, mandatory=False):
        """
        Get workflow input parameter names.

        Args:
            mandatory: If True, only return mandatory inputs (no default value)

        Returns:
            list: List of input parameter names
        """
        return self.workflow.get_workflow_inputs(mandatory=mandatory)

    def get_max_cores(self):
        """
        Get the maximum number of cores from CWL ResourceRequirements.

        Returns:
            int: Maximum cores requested, or default from environment
        """
        resources = self.workflow.eval_resource()
        max_cores = max(resources["coresMax"]) if resources["coresMax"] else None

        if max_cores is None:
            max_cores = int(os.environ.get("DEFAULT_MAX_CORES", "2"))

        return max_cores

    def get_max_ram(self):
        """
        Get the maximum RAM in megabytes from CWL ResourceRequirements.

        Returns:
            str: Maximum RAM in MB with unit (e.g., "4096Mi")
        """
        resources = self.workflow.eval_resource()
        max_ram = max(resources["ramMax"]) if resources["ramMax"] else None

        if max_ram is None:
            max_ram = int(os.environ.get("DEFAULT_MAX_RAM", "4096"))

        # Return as string with Mi unit
        return f"{max_ram}Mi"

    def get_volume_size(self, unit="Mi"):
        """
        Get the volume size for temporary and output directories.

        Calculates based on tmpdir and outdir requirements from CWL.

        Args:
            unit: Unit for volume size ('Gi' for Gigabytes or 'Mi' for Megabytes)

        Returns:
            str: Volume size with unit (e.g., "10Gi" or "10240Mi")
        """
        resources = self.workflow.eval_resource()

        # Get max tmpdir and outdir in MB
        # Use Max if available, otherwise fall back to Min
        tmpdir_max = max(resources["tmpdirMax"]) if resources["tmpdirMax"] else (max(resources["tmpdirMin"]) if resources["tmpdirMin"] else 0)
        outdir_max = max(resources["outdirMax"]) if resources["outdirMax"] else (max(resources["outdirMin"]) if resources["outdirMin"] else 0)

        # Total in MB
        volume_size_mb = tmpdir_max + outdir_max

        if volume_size_mb == 0:
            # Default from environment
            default = os.environ.get("DEFAULT_VOLUME_SIZE", "10Gi")
            # If default doesn't match requested unit, convert
            if unit not in default:
                return f"10{unit}"
            return default

        # Convert based on requested unit
        if unit == "Gi":
            # Convert MB to Gi (1 Gi = 1024 Mi)
            volume_size = int(volume_size_mb / 1024) + 1
        else:  # Mi
            volume_size = volume_size_mb

        return f"{volume_size}{unit}"

    def assert_parameters(self, mandatory=True):
        """
        Validate that required workflow inputs are provided.

        Args:
            mandatory: If True, check only mandatory inputs

        Returns:
            bool: True if all required inputs are present, False otherwise
        """
        try:
            required_inputs = self.get_workflow_inputs(mandatory=mandatory)

            for required_input in required_inputs:
                if required_input not in self.inputs.inputs:
                    error_msg = f"Missing required input: {required_input}"
                    logger.error(error_msg)
                    return False

            logger.info("All required parameters are present")
            return True
        except Exception as e:
            logger.error(f"Error checking parameters: {e}")
            return False

    def get_processing_parameters(self):
        """
        Get processing parameters from inputs.

        Returns:
            dict: Processing parameters suitable for CWL execution
        """
        return self.inputs.get_processing_parameters(workflow=self.workflow.get_workflow())

    @abstractmethod
    def wrap(self):
        """
        Wrap the CWL workflow with stage-in/stage-out steps.
        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement wrap()")

    @abstractmethod
    def execute(self):
        """
        Execute the CWL workflow.
        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement execute()")
