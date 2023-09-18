import sys
import shlex
import os
import yaml
import itertools
import rich_click as click
from .misc import float_range
from .logging import setup_logger


logger = setup_logger()


def get_values_nested_dict(d: dict) -> list:
    """Get a list of all the values in a nested dictionary.

    :param d: The nested dictionary.
    :type d: dict

    :return: A list of all the values in a nested dictionary.
    :rtype: list
    """
    return list(itertools.chain.from_iterable(
        [get_values_nested_dict(v) if isinstance(v, dict) else [v]
         for v in d.values()]))


def check_arguments_yaml_file(
        parameters_file_content: dict) -> bool:
    """Check if the arguments in the YAML file are all given in
    correct format.

    :param parameters_file_content: The content of the parameters file.
    :type parameters_file_content: dict

    :return: True if all the arguments are given, False otherwise.
    :rtype: bool
    """

    # Check if any key from "fixed_args" or "varying_args" is
    # given
    check = any([k in parameters_file_content for k in [
        "fixed_args", "varying_args"]])

    # Check if all given keys are not assigned a None value
    check = check and all([v is not None for v in get_values_nested_dict(
        parameters_file_content)])

    return check


def get_arguments_yaml_file_content(
        parameters_file_content: dict,
        type_arg: str) -> tuple:
    """Get a list of all the positional arguments position or
    options names in the parameters file content.

    :param parameters_file_content: The content of the parameters file.
    :type parameters_file_content: dict

    :param type_arg: The type of the arguments to get.
    :type type: str

    :return: A tuple of all the arguments (fixed, groups and range) position
             or options names.
    :rtype: tuple
    """

    # If empty return empty list
    if len(parameters_file_content) == 0:
        return [], [], []

    arguments_fixed = []
    if "fixed_args" in parameters_file_content:
        if type_arg in parameters_file_content["fixed_args"]:
            arguments_fixed = \
                    parameters_file_content['fixed_args'][type_arg].items()

    arguments_groups = []
    arguments_range = []
    if "varying_args" in parameters_file_content:
        if "groups" in parameters_file_content["varying_args"]:
            for group in parameters_file_content["varying_args"][
                    "groups"]:
                if type_arg in group:
                    arguments_groups.append(
                            group[type_arg].items())

        if "range" in parameters_file_content["varying_args"]:
            if type_arg in parameters_file_content["varying_args"][
                    "range"]:
                arguments_range = \
                        parameters_file_content["varying_args"][
                                "range"][type_arg].items()

    return list(arguments_fixed), list(arguments_groups), \
        list(arguments_range)


def check_positional_arguments_compatibility(
        parameters_file_content: dict) -> bool:
    """Check if the positional arguments are compatible in the
    parameters file content.

    :param parameters_file_content: The content of the parameters file.
    :type parameters_file_content: dict

    :return: True if the positional arguments are compatible in the
             parameters file content, False otherwise.
    :rtype: bool
    """

    arguments_fixed, arguments_groups, arguments_range = \
        get_arguments_yaml_file_content(
                parameters_file_content, "positional")

    # For each group we don't exepct that the same positional
    # argument is given than the others so we have to check
    # compatibility between fixed, one group and all range
    check_ok = True
    for group in arguments_groups:
        positional_args_items = itertools.chain.from_iterable(
                [arguments_fixed, group, arguments_range])
        positional_args_positions = [pos for pos, _ in positional_args_items]
        if len(positional_args_positions) == 0:
            continue
        elif any([pos < 0 for pos in positional_args_positions]):
            check_ok = False
            break
        else:
            check_ok = len(positional_args_positions) == \
                    len(set(positional_args_positions))
            if not check_ok:
                break

    return check_ok


def check_options_compatibility(
        parameters_file_content: dict) -> bool:
    """Check if the options are compatible in the parameters file
    content.

    :param parameters_file_content: The content of the parameters file.
    :type parameters_file_content: dict

    :return: True if the options are compatible in the parameters
             file content, False otherwise.
    :rtype: bool
    """
    arguments_fixed, arguments_groups, arguments_range = \
        get_arguments_yaml_file_content(
                parameters_file_content, "options")

    # For each group we don't exepct that the same positional
    # argument is given than the others so we have to check
    # compatibility between fixed, one group and all range
    check_ok = True
    for group in arguments_groups:
        options_items = itertools.chain.from_iterable(
                [arguments_fixed, group, arguments_range])
        options_names = [name for name, _ in options_items]

        if len(options_names) == 0:
            continue
        elif any([not name.startswith("--") for name in options_names]):
            check_ok = False
            break
        else:
            check_ok = len(options_names) == len(set(options_names))
            if not check_ok:
                break

    return check_ok


def parse_yaml_command_file(param_file: str) -> list:
    """Parse a YAML command file to a list of commands.

    :param file_path: The path of the YAML command file.
    :type file_path: str

    :return: The list of commands.
    :rtype: list
    """

    with open(param_file, "r") as f:
        param_file_content = yaml.safe_load(f)


    if not check_arguments_yaml_file(param_file_content):
        logger.error("The arguments are not given in correct format"
                     " in the parameters file content:\n"
                     f" {param_file_content}")
        sys.exit(1)

    if not check_positional_arguments_compatibility(param_file_content):
        logger.error("The positional arguments are not compatible in"
                     " the parameters file content:\n"
                     f" {param_file_content}")
        sys.exit(1)

    if not check_options_compatibility(param_file_content):
        logger.error("The options are not compatible in the parameters"
                     " file content:\n"
                     f" {param_file_content}")
        sys.exit(1)

    # Starting with fixed arguments to construct command base
    fixed_args = {}
    if 'fixed_args' in param_file_content:


        # Positional arguments
        if 'positional' in param_file_content['fixed_args']:
            for pos, value in param_file_content['fixed_args']['positional'].items():
                fixed_args[f'pos_{pos}'] = value

        # Options arguments
        if 'options' in param_file_content['fixed_args']:
            for opt, value in param_file_content['fixed_args']['options'].items():
                fixed_args[opt] = value

    # Now we have to deal with varying arguments
    final_commands = []
    if 'varying_args' in param_file_content:

        # Transforming range into groups
        groups_range = []
        if 'range' in param_file_content['varying_args']:

            # Positional arguments
            if 'positional' in param_file_content['varying_args']['range']:
                for pos, range_list in \
                    param_file_content['varying_args']['range']['positional'].items():
                    if len(range_list) != 3:
                        logger.error("The range positional argument"
                                     f" {pos} {range_list} is not valid.")
                        sys.exit(1)

                    groups_range += [{f'pos_{pos}': value}
                               for value in float_range(*range_list)]

            # Options arguments
            if 'options' in param_file_content['varying_args']['range']:

                for opt, range_list in \
                    param_file_content['varying_args']['range']['options'].items():
                    if len(range_list) != 3:
                        logger.error("The range option"
                                     f" {opt} {range_list} is not valid.")
                        sys.exit(1)

                    if len(groups_range) == 0:
                        groups_range += [{opt: value}
                               for value in float_range(*range_list)]
                    else:
                        new_groups_range = []
                        for value in float_range(*range_list):
                            for group in groups_range:
                                new_group = {opti: value_group for opti, value_group
                                             in group.items()}
                                new_group[opt] = value
                                new_groups_range.append(new_group)
                        groups_range = new_groups_range

        # Taking care of groups
        groups_groups = []
        if 'groups' in param_file_content['varying_args']:

            for group in param_file_content['varying_args']['groups']:

                thisgroup = {}
                # Positional arguments
                if 'positional' in group:
                    for pos, value in group['positional'].items():
                        thisgroup[f'pos_{pos}'] = value

                # Options arguments
                if 'options' in group:
                    for opt, value in group['options'].items():
                        thisgroup[opt] = value

                groups_groups.append(thisgroup)


        # Now we have to do a Cartesian product of everything: range groups and
        # groups groups
        if len(groups_range) == 0:
            final_commands = [{**fixed_args, **group_group}
                              for group_group in groups_groups]

        elif len(groups_groups) == 0:
            final_commands = [{**fixed_args, **range_group}
                              for range_group in groups_range]

        else:
            cartesian_product = itertools.product(groups_range, groups_groups)
            for range_group, group_group in cartesian_product:
                final_commands.append({**fixed_args, **range_group, **group_group})


    else:
        # No varying arguments
        final_commands = [fixed_args]

    return final_commands


def parse_args_string(args: str) -> list:
    """Parse a string of arguments to a list of arguments.

    :param args: The string of arguments to parse.
    :type args: str

    :return: The list of arguments.
    :rtype: list
    """

    # Find first non space character
    i = 0
    while i < len(args) and args[i] == " ":
        i += 1

    # Parse the string of arguments
    result = []
    while i < len(args):
        if args[i] == " ":
            i += 1
        elif args[i] == '-' and args[i+1] == '-':
            j = i+2
            while j < len(args) and args[j] != " ":
                j += 1
            result.append(args[i:j])
            i = j
        else:
            j = i+1
            while j < len(args) and args[j] != " ":
                j += 1
            result.append(args[i:j])
            i = j

    return result


def get_absolute_path(path: str) -> str:
    """Get the absolute path of a path.
    Verify if path is relative or absolute. If relative,
    get the absolute path from the current working directory.

    :param path: The path to get the absolute path.
    :type path: str

    :return: The absolute path.
    :rtype: str
    """

    if not os.path.isabs(path):
        return os.path.abspath(path)

    return path


def parse_group_parameters(group_parameters: dict) -> list:
    """Parse dictionary of parameters of a run to
    a list to pass as arguments to subprocess.

    :param group_parameters: Dictionary of parameters
    :type group_parameters: dict

    :return: List of parameters
    :rtype: list
    """

    list_pos_arguments = []
    list_options = []
    for key, value in group_parameters.items():

        # Positional arguments
        if not key.startswith('--'):
            list_pos_arguments.append(value)
        else:
            if isinstance(value, list):
                for v in value:
                    list_options += [key, v]
            else:
                list_options += [key, value]

    return list_pos_arguments + list_options


def parse_positional_optional_arguments(
        parameters: list, pos_shift: int = 0) -> dict:
    """Parse the positional and optional arguments depending on
    if there is -- or not in the string of the parameters.

    :param parameters: The parameters to parse.
    :type parameters: list

    :param pos_shift: The shift of the positional arguments.
    :type pos_shift: int

    :return: A dictionary of the parsed parameters.
    :rtype: dict
    """

    # Parse the string of the group by splitting
    # it with the space character
    i = 0
    pos_number = pos_shift
    result = {}
    while i < len(parameters):
        if parameters[i].startswith("--"):

            isflag = False
            if i == len(parameters)-1:
                isflag = True
            else:
                isflag = parameters[i+1].startswith("--")

            # check if a flag
            if isflag:
                isflag = True
                value = ""
            else:
                value = parameters[i+1]

            if parameters[i] not in result:
                result[parameters[i]] = value
            else:
                if isinstance(result[parameters[i]], list):
                    result[parameters[i]].append(value)
                else:
                    result[parameters[i]] = [result[parameters[i]],
                                             value]
            if isflag:
                i += 1
            else:
                i += 2
        else:
            result[f"pos_{pos_number}"] = parameters[i]
            pos_number += 1
            i += 1

    return result


def parse_args_cli(ctx: click.Context, groups_of_parameters: list = [],
                   range_of_parameters: list = [],
                   runner_params_to_get: list =
                   ["--n_threads", "--submit_template",
                    "--wait", "--gpu"]) -> tuple:
    """Parse the arguments of the CLI and return a list of dictionary of them.
    The arguments are parsed from the context of the CLI and the groups
    of parameters.


    :param ctx: The context of the CLI.
    :type ctx: click.Context

    :param groups_of_parameters: The groups of parameters to parse.
    :type groups_of_parameters: list

    :param runner_params_to_get: The parameters of the runner to get.
    :type runner_params_to_get: list

    :return: A tuple of the parsed parameters and the runner parameters.
    :rtype: tuple
    """

    # Get the arguments from the context
    fixed_args = parse_positional_optional_arguments(ctx.args)

    # Remove the runner params in a separate list
    runner_params = {}
    for param in runner_params_to_get:
        if param in fixed_args:
            runner_params[param] = fixed_args[param]
            del fixed_args[param]

    # Parse the arguments of the groups of parameters
    if len(groups_of_parameters) == 0:
        parsed_parameters = [fixed_args]
    else:
        parsed_parameters = []
        for group in groups_of_parameters:
            # Find the shift needed in the key of positional
            # arguments
            pos_shift = 0
            for key in fixed_args.keys():
                if key.startswith("pos_"):
                    pos_shift = max(pos_shift, int(key[-1]))

            # Parse the string of the group by splitting
            # it with the space character
            group = shlex.split(group, posix=False)
            varying_parameters = \
                parse_positional_optional_arguments(
                    group,
                    pos_shift=int(pos_shift)+1
                )
            parsed_parameters.append({**fixed_args, **varying_parameters})

    # Parse the arguments of the range of parameters
    if len(range_of_parameters) >= 1:
        for range_param in range_of_parameters:
            new_parsed_parameters = []

            values = range_param.strip().split(" ")
            if len(values) != 4:
                raise ValueError(
                    f"Range parameter {range_param} not well formatted")

            # Get the name of the parameter, the start, the end and the step
            name = values[0]
            start = float(values[1])
            end = float(values[2])
            step = float(values[3])

            # Check if the parameter is already in the parsed parameters
            if name in parsed_parameters[0]:
                raise ValueError(
                    f"Parameter {name} already in the parsed parameters")

            # Check it is not a positional argument
            if not name.startswith("--"):
                raise ValueError(
                    f"Parameter {name} is not an optional argument")

            # Add the parameter to the parsed parameters
            # with the values of the range
            generator = float_range(start, end, step)
            for value in generator:
                for parsed_param in parsed_parameters:
                    new_parsed_parameters.append(
                        {**parsed_param, name: str(value)}
                    )
            parsed_parameters = new_parsed_parameters

    return parsed_parameters, runner_params


# Document file parsing
# =====================
def parse_document_file(document_file: str) -> dict:
    """Parse the document file specified in YAML format.

    :param document_file: The path to the document file.
    :type document_file: str

    :return: The dictionary of the document file.
    :rtype: dict
    """

    with open(document_file, "r") as f:
        document = yaml.load(f, Loader=yaml.FullLoader)

    # Check the document file is well formatted
    if "name" not in document:
        raise ValueError("Document file must contain a name")

    if "description" not in document:
        raise ValueError("Document file must contain a description")

    if "path" not in document:
        raise ValueError("Document file must contain a path")

    if "compile_script" not in document:
        raise ValueError("Document file must contain a compile_script")

    if "compile_script_command" not in document:
        logger.warning("No compile command specified in the document file. "
                       "Defaulted as make")
        document["compile_script_command"] = "make"

    if "experiment_dependencies" in document:

        # Check wheter a list
        if not isinstance(document["experiment_dependencies"], list):
            raise ValueError("Experiment dependencies must be a list")

        # Check whether the dependencies are well formatted
        for dependency in document["experiment_dependencies"]:

            if "experiment_name" not in dependency:
                raise ValueError("Experiment dependency must contain "
                                 "an experiment name")
            experiment_name = dependency["experiment_name"]

            if "run_args_file" not in dependency:
                logger.info("No run_args_file specified in the document file "
                            f"for experiment {experiment_name}")
                dependency["run_args_file"] = None

            if "runner" not in dependency:
                logger.warning("No runner specified for experiment "
                               f"{experiment_name}. Defaulted as local")
                document["runner"] = "local"

            if "container" not in dependency:
                document["container"] = None

            if "runner_params" not in dependency:
                dependency["runner_params"] = None

            if 'action_name' not in dependency:
                dependency['action_name'] = None

            if 'action_params' not in dependency:
                dependency['action_params'] = ""

            if "files" not in dependency:
                dependency["files"] = []
            else:
                if not isinstance(dependency["files"], list):
                    raise ValueError("Files dependency must be a list")
                for file in dependency["files"]:
                    if not isinstance(file, str):
                        raise ValueError("Files dependency must be a list "
                                         "of strings")

    if "view_script" not in document:
        logger.warning("No view_script specified in the document file.")
        document["view_script"] = None

    if "view_script" in document and \
            "view_script_command" not in document:
        raise ValueError(
                "View script must be associated with a view_script_command")

    return document


# Dataset file parsing
# ====================
def parse_dataset_file(dataset_file: str) -> dict:
    """Parse the dataset file specified in YAML format.

    :param dataset_file: The path to the dataset file.
    :type dataset_file: str

    :return: The dictionary of the dataset file.
    :rtype: dict
    """

    with open(dataset_file, "r") as f:
        dataset = yaml.load(f, Loader=yaml.FullLoader)

    # Check the dataset file is well formatted
    if "name" not in dataset:
        raise ValueError("Dataset file must contain a name")

    if "description" not in dataset:
        raise ValueError("Dataset file must contain a description")

    if "path" not in dataset:
        raise ValueError("Dataset file must contain a path")

    # Fill the missing fields
    if "tags" not in dataset:
        dataset["tags"] = []

    return dataset
