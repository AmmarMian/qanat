# ========================================
# FileName: containers.py
# Date: 23 mai 2023 - 10:40
# Author: Ammar Mian
# Email: ammar.mian@univ-smb.fr
# GitHub: https://github.com/ammarmian
# Brief: Manage execution inside containers
# =========================================

import shutil


def check_apptainer_installed():
    """Check if apptainer is installed
    and a cli command

    :return: True if apptainer is installed
    :rtype: bool
    """
    return shutil.which("apptainer") is not None


def check_singularity_installed():
    """Check if singularity is installed
    and a cli command

    :return: True if singularity is installed
    :rtype: bool
    """
    return shutil.which("singularity") is not None


def check_docker_installed():
    """Check if docker is installed
    and a cli command

    :return: True if docker is installed
    :rtype: bool
    """
    return shutil.which("docker") is not None


def get_container_technology(container_path: str):
    """Get the container technology used.

    :param container_path: Path to the container
    :type container_path: str

    :return: The container technology used
    :rtype: str
    """

    if container_path.endswith(".sif"):
        if check_apptainer_installed():
            return "apptainer"
        elif check_singularity_installed():
            return "singularity"
    elif container_path.endswith("Dockerfile"):
        return "docker"

    raise ValueError(f"Unknown container type: {container_path}")


def get_container_run_command(container_path: str,
                              command: list,
                              bind_paths: dict = {}) -> list:
    """Get the command to run a container.

    :param container_path: Path to the container
    :type container_path: str

    :param command: Command to run inside the container
    :type command: list

    :param bind_paths: Paths to bind inside the container
    :type bind_paths: dict

    :param rel_path_offset: Relative path offset to the bind_paths
    :type rel_path_offset: str

    :return: The command to run the container
    :rtype: list
    """

    container_technology = get_container_technology(container_path)
    if container_technology in ["apptainer", "singularity"]:
        run_command = [container_technology, 'run']
        for bind_path in bind_paths:
            run_command += ["--bind",
                            f"{bind_path}:{bind_paths[bind_path]}"]
        run_command += [container_path]
        run_command += command
    else:
        raise NotImplementedError(
                "Sorry, "
                f"Container technology {container_technology} not implemented")

    return run_command
