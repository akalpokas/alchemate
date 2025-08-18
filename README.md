[![Build and test](https://github.com/akalpokas/alchemate/actions/workflows/ci.yml/badge.svg?event=workflow_dispatch)](https://github.com/akalpokas/alchemate/actions/workflows/ci.yml)

# alchemate
Modular [SOMD2](https://github.com/OpenBioSim/somd2) processing workflows.

# Purpose
Alchemate implements and abstracts high-level functionality to SOMD2 FEP engine, such as iterative λ-schedule optimization or simulation convergence detection for example. The framework is designed to be modular and extensible which allows for arbitrary workflows to be written and plugged in easily.

# Usage
Using alchemate involves creating a SOMD2 configuration object, defining a simulation workflow, and creating a manager which will run the specified workflows sequentially:

```python
from somd2.config import Config as somd2_config
from alchemate.manager import WorkflowManager

# Import the modular workflows you need for the calculation
from alchemate.steps.preprocessing import OptimizeExchangeProbabilities

# Define SOMD2 configuration for setting up the physical simultion 
somd2_config = somd2_config()
somd2_config.cutoff_type = "PME"
somd2_config.cutoff = "14A"
somd2_config.replica_exchange = True

# Define the desired workflow
simulation_workflow = [
    OptimizeExchangeProbabilities(optimization_attempts=3),
]

# Create the manager with this workflow
manager = WorkflowManager(workflow_steps=simulation_workflow)

# Run everything
context = manager.execute(system="merged_molecule.s3", somd2_config=somd2_config)
```

At the heart of alchemate is the `SimulationContext` class which gets passed through workflows sequentially and updated. This for example can be used to attempt and pre-optimize λ-schedule of a transformation in vacuum before passing the context to the main simulation:

ADD CODE EXAMPLE

Or a further post-processing workflow can be plugged in to test for simulation convergence:

ADD CODE EXAMPLE - show customization


Head to [examples](examples/) for more detailed scripts.
___
# Installation

To install alchemate, please first install [SOMD2](https://github.com/OpenBioSim/somd2) into your conda environment. Then you can install the package into your environment by cloning this repository, and running:
```bash
pip install -e .
```
