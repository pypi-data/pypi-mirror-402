# zoo-runner-common

A shared utility library for ZOO-Project CWL runners – centralizing reusable components across runners like **Calrissian**, **Argo Workflows**, and **WES**.

---

## Overview

The `zoo-runner-common` repository provides core shared components used across multiple ZOO CWL runners. It **eliminates code duplication** by hosting:

- **Common base class** (`BaseRunner`) with 8+ shared methods
- **Zoo-specific configuration handlers** (`ZooConf`, `ZooInputs`, `ZooOutputs`)
- **CWL workflow parsing** and resource evaluation (`CWLWorkflow`)
- **Execution handler interface** (`ExecutionHandler`) for hooks
- **Service stubs** (`ZooStub`) to communicate with ZOO kernel

### Key Benefits

- ✅ **~437 lines of code duplication eliminated** across 3 runners
- ✅ **Single source of truth** for common functionality
- ✅ **Easier maintenance** - fix once, benefit everywhere
- ✅ **Consistent behavior** across all runners

---

## Directory Structure

```
zoo-runner-common/
├── base_runner.py      # Abstract BaseRunner with common methods
├── zoo_conf.py         # ZooConf, ZooInputs, ZooOutputs, CWLWorkflow
├── handlers.py         # ExecutionHandler abstract base class
├── zoostub.py          # ZooStub for ZOO kernel communication
└── __init__.py         # Package initialization
```

---

## Installation

### As a dependency (recommended)

Add to your runner's `pyproject.toml`:

```toml
[project]
dependencies = [
    "zoo-runner-common @ git+https://github.com/ZOO-Project/zoo-runner-common.git@main",
]
```

### Local development

```bash
export PYTHONPATH="$PYTHONPATH:/path/to/zoo-runner-common"
```

Or use relative imports:

```python
import sys
sys.path.insert(0, os.path.abspath('../zoo-runner-common'))
from base_runner import BaseRunner
from zoo_conf import ZooConf, ZooInputs, ZooOutputs, CWLWorkflow
from handlers import ExecutionHandler
```

---

## Components

### BaseRunner (base_runner.py)

Abstract base class providing common functionality for all CWL runners:

**Methods provided:**
- `get_workflow_id()` - Get workflow identifier
- `get_workflow_inputs(mandatory=False)` - Get workflow input parameters
- `get_max_cores()` - Get maximum CPU cores from CWL
- `get_max_ram()` - Get maximum RAM from CWL
- `get_volume_size(unit='Gi')` - Calculate volume size (supports Mi/Gi)
- `assert_parameters(mandatory=True)` - Validate required inputs
- `get_processing_parameters()` - Get execution parameters
- `get_namespace_name()` - Generate unique namespace name
- `update_status(progress, message)` - Update execution status
- `prepare()` - Pre-execution preparation with hooks
- `finalize(log, output, usage_report, tool_logs)` - Post-execution finalization

**Abstract methods (to implement):**
- `wrap()` - Wrap CWL with stage-in/stage-out
- `execute()` - Execute the workflow

### Zoo Configuration Classes (zoo_conf.py)

| Class | Description |
|-------|-------------|
| `ZooConf` | Wraps ZOO configuration dictionary |
| `ZooInputs` | Handles input parameter conversion and validation |
| `ZooOutputs` | Manages output parameters |
| `CWLWorkflow` | Parses CWL, evaluates resources, handles scatter |
| `ResourceRequirement` | CWL resource hints dataclass |

**Key Features:**
- Advanced type conversion (int, float, bool, arrays)
- File handling with format metadata
- OGC bounding box support
- NULL value handling
- Array inputs with `isArray`

### ExecutionHandler (handlers.py)

Abstract base class for execution customization:

```python
class ExecutionHandler(ABC):
    @abstractmethod
    def pre_execution_hook(self): pass
    
    @abstractmethod
    def post_execution_hook(self, log, output, usage_report, tool_logs): pass
    
    @abstractmethod
    def get_secrets(self): pass
    
    @abstractmethod
    def get_pod_env_vars(self): pass
    
    @abstractmethod
    def get_pod_node_selector(self): pass
    
    @abstractmethod
    def handle_outputs(self, log, output, usage_report, tool_logs): pass
    
    @abstractmethod
    def get_additional_parameters(self): pass
```

---

## Usage Example

```python
from zoo_runner_common.base_runner import BaseRunner
from zoo_runner_common.handlers import ExecutionHandler

class MyCustomRunner(BaseRunner):
    def wrap(self):
        # Implement CWL wrapping logic
        return wrapped_cwl
    
    def execute(self):
        # Prepare execution
        cwljob = self.prepare()
        
        # Execute workflow (custom logic)
        result = my_executor.run(cwljob.cwl, cwljob.params)
        
        # Finalize
        self.finalize(log, output, usage_report, tool_logs)
        return result
```

---

## Runners Using zoo-runner-common

| Runner | Backend | Repository |
|--------|---------|------------|
| **zoo-calrissian-runner** | Calrissian/Kubernetes | [EOEPCA/zoo-calrissian-runner](https://github.com/EOEPCA/zoo-calrissian-runner) |
| **zoo-argowf-runner** | Argo Workflows | [ZOO-Project/zoo-argowf-runner](https://github.com/ZOO-Project/zoo-argowf-runner) |
| **zoo-wes-runner** | WES/TOIL | [ZOO-Project/zoo-wes-runner](https://github.com/ZOO-Project/zoo-wes-runner) |

---

## Module Reference

| Module |	Description |
| ---- | -------- |
| BaseRunner |	Abstract runner blueprint all runners must extend |
| ZooConf |	Parses conf.json, manages job ID, state |
| ZooInputs |	Parses inputs.json, formats CWL-style parameters |
| ZooOutputs |	Handles writing and setting output results |
| CWLWorkflow |	Loads, parses, and analyzes CWL workflows |
| ResourceRequirement |	Parses and evaluates CWL resource hints/requirements |
| wrapper_utils |	Provides helper to build wrapped CWL pipeline |
| ZooStub |	Interacts with ZOO's lenv for progress updates |

---

## Used By
- zoo-wes-runner
- zoo-argowf-runner
- zoo-calrissian-runner
