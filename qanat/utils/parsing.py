import os
import rich_click as click
from .misc import float_range


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
