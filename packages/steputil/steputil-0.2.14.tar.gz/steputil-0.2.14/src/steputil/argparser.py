"""Command-line argument parser with builder pattern for pipeline steps."""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable


class InputField:
    """Represents an input file field with JSONL reading capability."""

    def __init__(self, path: Optional[str]):
        """Initialize an input field with a file path.

        Args:
            path: Path to the input file. Can be None for optional inputs.
        """
        self.path = path

    def readJsons(self) -> List[Dict[str, Any]]:
        """Read JSONL file and return list of JSON objects.

        Returns:
            List of dictionaries representing JSON objects from the file.
            Returns empty list if path is None (optional input not provided).

        Raises:
            FileNotFoundError: If the input file doesn't exist.
            json.JSONDecodeError: If a line contains invalid JSON.
        """
        if self.path is None:
            return []

        result = []
        with open(self.path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line:  # Skip empty lines
                    try:
                        result.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        raise json.JSONDecodeError(
                            f"Invalid JSON on line {line_num}: {e.msg}", e.doc, e.pos
                        )
        return result


class OutputField:
    """Represents an output file field with JSONL writing capability."""

    def __init__(self, path: Optional[str]):
        """Initialize an output field with a file path.

        Args:
            path: Path to the output file. Can be None for optional outputs.
        """
        self.path = path

    def writeJsons(
        self, jsons: List[Dict[str, Any]], filename: Optional[str] = None
    ) -> None:
        """Write list of JSON objects to JSONL file.

        Args:
            jsons: List of dictionaries to write as JSON lines.
            filename: Optional filename for batching scenarios. If provided,
                self.path is treated as a directory and the file is written
                to self.path/filename.

        Note:
            If path is None (optional output not provided), this method does nothing.
        """
        if self.path is None:
            return

        # Determine the actual output path
        if filename is not None:
            # Treat self.path as a directory
            output_path = Path(self.path) / filename
            # Create directory if it doesn't exist
            output_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            # Treat self.path as a file path
            output_path = Path(self.path)
            # Create parent directory if it doesn't exist
            output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            for obj in jsons:
                f.write(json.dumps(obj, ensure_ascii=False, default=str) + "\n")


class Config:
    """Container for configuration values."""

    pass


class StepArgs:
    """Container for parsed command-line arguments with input/output fields."""

    def __init__(
        self,
        args_dict: Dict[str, Optional[str]],
        input_names: List[str],
        output_names: List[str],
        config_obj: Optional[Config] = None,
        dynamic_inputs: Optional[Dict[str, str]] = None,
        dynamic_outputs: Optional[Dict[str, str]] = None,
    ):
        """Initialize StepArgs with parsed arguments.

        Args:
            args_dict: Dictionary of argument name to value
                (can be None for optional inputs).
            input_names: List of input field names.
            output_names: List of output field names.
            config_obj: Optional Config object with configuration values.
            dynamic_inputs: Optional dictionary of dynamic input names to paths.
            dynamic_outputs: Optional dictionary of dynamic output names to paths.
        """
        # Store input and output names for reference
        self.input_names = input_names
        self.output_names = output_names

        # Create InputField objects for each input
        for name in input_names:
            setattr(self, name, InputField(args_dict.get(name)))

        # Create OutputField objects for each output
        for name in output_names:
            setattr(self, name, OutputField(args_dict.get(name)))

        # Set config object if provided
        if config_obj is not None:
            self.config = config_obj

        # Set dynamic inputs/outputs if provided
        if dynamic_inputs is not None:
            self.inputs = dynamic_inputs
        if dynamic_outputs is not None:
            self.outputs = dynamic_outputs

    def get_inputs(self):
        """Get dictionary of input paths.

        If dynamic inputs are enabled, returns the dynamic inputs dictionary.
        Otherwise, returns a dictionary with paths from regular inputs.

        Returns:
            Dictionary mapping input names to paths (e.g., {'input': '/path/to/file', 'actions': '/path/to/actions'})
        """
        if hasattr(self, 'inputs') and self.inputs:
            # Return dynamic inputs dictionary
            return self.inputs
        else:
            # Return regular inputs as a dictionary
            result = {}
            for name in self.input_names:
                field = getattr(self, name, None)
                if field and field.path:
                    result[name] = field.path
            return result

    def get_outputs(self):
        """Get dictionary of output paths.

        If dynamic outputs are enabled, returns the dynamic outputs dictionary.
        Otherwise, returns a dictionary with paths from regular outputs.

        Returns:
            Dictionary mapping output names to paths (e.g., {'output': '/path/to/file', 'results': '/path/to/results'})
        """
        if hasattr(self, 'outputs') and self.outputs:
            # Return dynamic outputs dictionary
            return self.outputs
        else:
            # Return regular outputs as a dictionary
            result = {}
            for name in self.output_names:
                field = getattr(self, name, None)
                if field and field.path:
                    result[name] = field.path
            return result


class _Sentinel:
    """Sentinel value to distinguish between None and unset default values."""

    pass


_UNSET = _Sentinel()


class StepArgsBuilder:
    """Builder for creating command-line argument parser with input/output fields."""

    def __init__(self):
        """Initialize the builder."""
        self._inputs: List[tuple[str, Optional[str], bool]] = (
            []
        )  # (field_name, original_name, optional)
        self._outputs: List[tuple[str, Optional[str], bool]] = (
            []
        )  # (field_name, original_name, optional)
        self._configs: List[tuple[str, bool, Any]] = []  # (name, optional, default)
        self._validation_callback: Optional[Callable[[Config], bool]] = None
        self._collect_dynamic_inputs: bool = False
        self._collect_dynamic_outputs: bool = False

    def input(
        self, name: Optional[str] = None, optional: bool = False
    ) -> "StepArgsBuilder":
        """Add an input field to the argument parser.

        Args:
            name: Name of the input parameter. If None, uses 'input'.
            optional: If True, the input argument is optional. Defaults to False.

        Returns:
            Self for method chaining.
        """
        field_name = name if name is not None else "input"
        self._inputs.append((field_name, name, optional))
        return self

    def output(
        self, name: Optional[str] = None, optional: bool = False
    ) -> "StepArgsBuilder":
        """Add an output field to the argument parser.

        Args:
            name: Name of the output parameter. If None, uses 'output'.
            optional: If True, the output argument is optional. Defaults to False.

        Returns:
            Self for method chaining.
        """
        field_name = name if name is not None else "output"
        self._outputs.append((field_name, name, optional))
        return self

    def inputs(self) -> "StepArgsBuilder":
        """Enable collection of all --input-<name> arguments.

        Results available in step.inputs as a dict mapping name to path.

        Returns:
            Self for method chaining.
        """
        self._collect_dynamic_inputs = True
        return self

    def outputs(self) -> "StepArgsBuilder":
        """Enable collection of all --output-<name> arguments.

        Results available in step.outputs as a dict mapping name to path.

        Returns:
            Self for method chaining.
        """
        self._collect_dynamic_outputs = True
        return self

    def config(
        self,
        name: str,
        optional: bool = False,
        default_value: Any = _UNSET,
    ) -> "StepArgsBuilder":
        """Add a configuration field.

        Args:
            name: Name of the configuration field (required).
            optional: Whether the field is optional. Defaults to False.
            default_value: Default value if not set in config file.

        Returns:
            Self for method chaining.
        """
        self._configs.append((name, optional, default_value))
        return self

    def validate(self, callback: Callable[[Config], bool]) -> "StepArgsBuilder":
        """Add a validation callback for configuration.

        Args:
            callback: Function that takes Config object and returns True if valid.

        Returns:
            Self for method chaining.
        """
        self._validation_callback = callback
        return self

    def _print_buildinfo(self) -> None:
        """Print buildinfo from /app/buildinfo file if it exists."""
        buildinfo_path = Path("/app/buildinfo")
        try:
            with open(buildinfo_path, "r", encoding="utf-8") as f:
                print(f.read().strip())
        except FileNotFoundError:
            pass  # Silently skip if file doesn't exist

    def build(self) -> StepArgs:
        """Build the argument parser and parse command-line arguments.

        If no command-line arguments are provided and inputs/outputs are defined,
        prints the contents of /app/README.md and exits.

        Returns:
            StepArgs object with parsed input/output fields.

        Raises:
            ValueError: If a required config field is missing or invalid.
        """
        # Print buildinfo at the start
        self._print_buildinfo()

        # Check if command line is empty and we have inputs/outputs defined
        if len(sys.argv) == 1:
            readme_path = Path("/app/README.md")
            try:
                with open(readme_path, "r", encoding="utf-8") as f:
                    print(f.read())
            except FileNotFoundError:
                print(f"README.md not found at {readme_path}", file=sys.stderr)
            sys.exit(0)

        parser = argparse.ArgumentParser(
            description="Pipeline step with configurable inputs and outputs"
        )

        # Add input arguments
        for field_name, original_name, is_optional in self._inputs:
            arg_name = f'--{field_name.replace("_", "-")}'
            parser.add_argument(
                arg_name,
                type=str,
                required=not is_optional,
                default=None if is_optional else argparse.SUPPRESS,
                help=f"Path to input file for {field_name}",
            )

        # Add output arguments
        for field_name, original_name, is_optional in self._outputs:
            arg_name = f'--{field_name.replace("_", "-")}'
            parser.add_argument(
                arg_name,
                type=str,
                required=not is_optional,
                default=None if is_optional else argparse.SUPPRESS,
                help=f"Path to output file for {field_name}",
            )

        # Add config argument if configs are defined
        if self._configs:
            parser.add_argument(
                "--config",
                type=str,
                required=True,
                help="Path to configuration JSON file",
            )

        # Parse arguments (use parse_known_args if we need to collect dynamic inputs/outputs)
        if self._collect_dynamic_inputs or self._collect_dynamic_outputs:
            args, unknown = parser.parse_known_args()
            args_dict = vars(args)

            # Parse dynamic inputs and outputs from unknown args
            dynamic_inputs_dict = {}
            dynamic_outputs_dict = {}

            # Parse unknown arguments into a dictionary
            unknown_args = {}
            i = 0
            while i < len(unknown):
                arg = unknown[i]
                if not arg.startswith("--"):
                    raise ValueError(f"Invalid argument format: {arg}")

                # Check if argument is in --key=value format
                if "=" in arg:
                    key_value = arg[2:]  # Remove "--" prefix
                    key, value = key_value.split("=", 1)  # Split on first "=" only
                    unknown_args[key] = value
                    i += 1
                else:
                    # Argument is in --key value format
                    if i + 1 >= len(unknown) or unknown[i + 1].startswith("--"):
                        raise ValueError(f"Missing value for argument {arg}")

                    key = arg[2:]  # Remove "--" prefix
                    value = unknown[i + 1]
                    unknown_args[key] = value
                    i += 2

            # Handle different cases based on whether both inputs and outputs are enabled
            if self._collect_dynamic_inputs and self._collect_dynamic_outputs:
                # Case: both .inputs() and .outputs() are called
                has_input = "input" in unknown_args
                has_output = "output" in unknown_args

                if has_input and has_output:
                    # Use --input as dynamic input and --output as dynamic output
                    # Expect no other arguments
                    if len(unknown_args) > 2:
                        extra_args = [k for k in unknown_args.keys() if k not in ["input", "output"]]
                        raise ValueError(f"Unexpected arguments when both --input and --output specified: {extra_args}")
                    dynamic_inputs_dict["input"] = unknown_args["input"]
                    dynamic_outputs_dict["output"] = unknown_args["output"]
                elif has_input:
                    # Use --input as dynamic input, all others as dynamic outputs
                    dynamic_inputs_dict["input"] = unknown_args["input"]
                    for key, value in unknown_args.items():
                        if key != "input":
                            dynamic_outputs_dict[key] = value
                elif has_output:
                    # Use --output as dynamic output, all others as dynamic inputs
                    dynamic_outputs_dict["output"] = unknown_args["output"]
                    for key, value in unknown_args.items():
                        if key != "output":
                            dynamic_inputs_dict[key] = value
                else:
                    # No --input or --output, split based on prefixes
                    for key, value in unknown_args.items():
                        if key.startswith("input-"):
                            name = key[6:]  # Remove "input-" prefix
                            dynamic_inputs_dict[name] = value
                        elif key.startswith("output-"):
                            name = key[7:]  # Remove "output-" prefix
                            dynamic_outputs_dict[name] = value
                        else:
                            raise ValueError(f"Ambiguous argument --{key}: must use --input-<name> or --output-<name> prefix")
            elif self._collect_dynamic_inputs:
                # Case: only .inputs() is called
                # Use all unknown args as dynamic inputs (no prefix required)
                dynamic_inputs_dict = unknown_args
            elif self._collect_dynamic_outputs:
                # Case: only .outputs() is called
                # Use all unknown args as dynamic outputs (no prefix required)
                dynamic_outputs_dict = unknown_args
        else:
            args = parser.parse_args()
            args_dict = vars(args)
            dynamic_inputs_dict = None
            dynamic_outputs_dict = None

        # Convert dashes back to underscores for field names
        normalized_dict = {k.replace("-", "_"): v for k, v in args_dict.items()}

        input_names = [name for name, _, _ in self._inputs]
        output_names = [name for name, _, _ in self._outputs]

        # Process config if defined
        config_obj = None
        if self._configs:
            config_path = normalized_dict.pop("config")
            config_data = self._load_config_file(config_path)
            config_obj = self._create_config_object(config_data)

            # Validate config if validation callback is provided
            if self._validation_callback is not None:
                if not self._validation_callback(config_obj):
                    raise ValueError("Configuration validation failed")

        return StepArgs(
            normalized_dict,
            input_names,
            output_names,
            config_obj,
            dynamic_inputs_dict if self._collect_dynamic_inputs else None,
            dynamic_outputs_dict if self._collect_dynamic_outputs else None,
        )

    def _load_config_file(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file.

        Args:
            config_path: Path to the configuration JSON file.

        Returns:
            Dictionary containing configuration data.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            json.JSONDecodeError: If config file contains invalid JSON.
        """
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("Config file must contain a JSON object")
            return data

    def _create_config_object(self, config_data: Dict[str, Any]) -> Config:
        """Create Config object from configuration data.

        Args:
            config_data: Dictionary containing configuration values.

        Returns:
            Config object with fields set according to config specifications.

        Raises:
            ValueError: If a required field is missing.
        """
        config_obj = Config()

        for name, optional, default_value in self._configs:
            if name in config_data:
                # Value exists in config file
                value = config_data[name]
            elif default_value is not _UNSET:
                # Use default value
                value = default_value
            elif optional:
                # Optional field without default
                value = None
            else:
                # Required field is missing
                raise ValueError(
                    f"Required configuration field '{name}' is missing "
                    f"from config file"
                )

            setattr(config_obj, name, value)

        return config_obj
