import sys
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
    arguments_fixed = []
    if "fixed_args" in parameters_file_content:
        if type_arg in parameters_file_content["fixed_args"]:
            arguments_fixed = \
                    parameters_file_content['fixed_args'][type_arg].items()

    arguments_groups = []
    arguments_range = []
    if "varying_args" in parameters_file_content:
        if "groups" in parameters_file_content["varying_args"]:
            if type_arg in parameters_file_content["varying_args"][
                    "groups"]:
                arguments_groups = \
                        parameters_file_content["varying_args"][
                                "groups"][type_arg].items()

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

    positional_args_items = itertools.chain.from_iterable(
            get_arguments_yaml_file_content(
                parameters_file_content, "positional"))
    positional_args_positions = [pos for pos, _ in positional_args_items]
    if len(positional_args_positions) == 0:
        return True
    elif any([pos < 0 for pos in positional_args_positions]):
        return False
    else:
        return len(positional_args_positions) == \
                len(set(positional_args_positions))


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

    options_items = itertools.chain.from_iterable(
            get_arguments_yaml_file_content(
                parameters_file_content, "options"))
    options_names = [name for name, _ in options_items]
    if len(options_names) == 0:
        return True
    elif any([not name.startswith("--") for name in options_names]):
        return False
    else:
        return len(options_names) == len(set(options_names))


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

    # Deal with positional arguments
    # --------------------------------
    fixed_pos_args, groups_pos_args, range_pos_args = \
        get_arguments_yaml_file_content(param_file_content, "positional")

    # Transform range positional arguments to groups positional arguments
    if len(range_pos_args) > 0:
        for pos, pos_range in range_pos_args:
            if len(pos_range) != 3:
                logger.error("The range positional argument"
                             f" {pos} {pos_range} is not valid.")
                sys.exit(1)
            groups_pos_args.append((pos, list(float_range(*pos_range))))

    # Get the order of the positional arguments (fixed and groups)
    # by sorting on the position
    fixed_pos_args_pos = {}
    groups_pos_args_pos = {}
    all_pos_args = sorted(fixed_pos_args + groups_pos_args,
                          key=lambda x: x[0])
    for i, (pos, _) in enumerate(all_pos_args):

        # Check whether in the fixed positional arguments
        if pos in [posi for posi, _ in fixed_pos_args]:
            fixed_pos_args_pos[pos] = i

        else:
            groups_pos_args_pos[pos] = i

    # Transform groups positional arguments to fixed positional arguments
    # By concatenating all the possible values of the groups positional
    # arguments using a Cartesian product
    if len(groups_pos_args) > 0:

        # Get the Cartesian product of all the possible values of the
        # groups positional arguments
        cartesian_product_group_pos = itertools.product(
                *[[(pos, value) for value
                   in values]
                  for pos, values in groups_pos_args]
        )

        pos_args = []
        for group_items in cartesian_product_group_pos:
            group_values = {
                f'pos_{fixed_pos_args_pos[pos]}': pos_values
                for pos, pos_values in fixed_pos_args
            }
            for pos, value in group_items:
                group_values[f'pos_{groups_pos_args_pos[pos]}'] = value
            pos_args.append(group_values)

    else:
        pos_args = [{f'pos_{fixed_pos_args_pos[pos]}': value
                     for pos, value in fixed_pos_args}]

    # Deal with options
    # --------------------------------
    fixed_opt_args, groups_opt_args, range_opt_args = \
        get_arguments_yaml_file_content(param_file_content, "options")

    # Transform range options to groups options
    if len(range_opt_args) > 0:
        for opt, opt_range in range_opt_args:
            if len(opt_range) != 3:
                logger.error("The range option"
                             f" {opt} {opt_range} is not valid.")
                sys.exit(1)
            groups_opt_args.append((opt, list(float_range(*opt_range))))

    # Transform groups options to fixed options by concatenating all the
    # possible values of the groups options using a Cartesian product
    if len(groups_opt_args) > 0:

        cartesian_product_group_opt = itertools.product(
                *[[(opt, value) for value
                   in values]
                  for opt, values in groups_opt_args]
        )

        opt_args = []
        for group_items in cartesian_product_group_opt:

            group_values = {
                opt: value
                for opt, value in fixed_opt_args
            }
            for opt, value in group_items:
                group_values[opt] = value
            opt_args.append(group_values)

    else:
        opt_args = [{opt: value
                     for opt, value in fixed_opt_args}]

    # Deal with both positional and options
    # We use a Cartesian product to get all the possible combinations
    # of the positional and options arguments
    # --------------------------------

    # Get the Cartesian product of all the possible values of the
    # positional and options arguments
    cartesian_product_pos_opt = itertools.product(pos_args, opt_args)
    params_final = []
    for pos_values, opt_values in cartesian_product_pos_opt:
        params_final.append({**pos_values, **opt_values})

    return params_final


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
            result[parameters[i]] = parameters[i+1]
            i += 2
        else:
            result[f"pos_{pos_number}"] = parameters[i]
            pos_number += 1
            i += 1

    return result


def parse_args_cli(ctx: click.Context, groups_of_parameters: list = [],
                   range_of_parameters: list = [],
                   runner_params_to_get: list =
                   ["--n_threads", "--submit_template"]) -> tuple:
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
            group = group.split(" ")
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
