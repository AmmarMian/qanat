# ========================================
# FileName: _constants.py
# Date: 03 mai 2023 - 11:17
# Author: Ammar Mian
# Email: ammar.mian@univ-smb.fr
# GitHub: https://github.com/ammarmian
# Brief: Constants used in the CLI
# =========================================

# --------------------------------------------------------
# General CLI Constants
# --------------------------------------------------------
CLI_NAME = "Qanat"
EXPERIMENT = ":bicycle:"
DATASET = ":floppy_disk:"
RUN = ":hourglass_flowing_sand:"
DESCRIPTION = ":speech_balloon:"
NAME = ":bookmark:"
PATH = ":file_folder:"
TAGS = ":label:"
ID = ":id:"
EXIT = ":door:"
HELP = ":question:"
YES = ":white_check_mark:"
NO = ":x:"
PROMPT = ":pencil:"

# --------------------------------------------------------
# Experiment CLI Constants
# --------------------------------------------------------
EXPERIMENT_NAME = NAME
EXPERIMENT_DESCRIPTION = DESCRIPTION
EXPERIMENT_PATH = PATH
EXPERIMENT_EXECUTABLE = ":gear:"
EXPERIMENT_EXECUTE_COMMAND = ":gear:"
EXPERIMENT_TAGS = TAGS
EXPERIMENT_DATASETS = DATASET
EXPERIMENT_ID = ID
EXPERIMENT_RUNS = RUN
EXPERIMENT_ACTION = ":hammer_and_wrench:"
RUN_IS_RUNNING = ":play_button:"
RUN_IS_FINISHED = ":white_check_mark:"
RUN_IS_FAILED = ":x:"
RUN_IS_PENDING = ":stopwatch:"
RUN_IS_PAUSED = ":pause_button:"
RUN_IS_UNKNOWN = ":question:"


def get_run_status_emoji(status):
    """Return the emoji corresponding to the status of the run."""
    if status == "running":
        emoji_status = f"{RUN_IS_RUNNING}"
    elif status == "finished":
        emoji_status = f"{RUN_IS_FINISHED}"
    elif status == "failed":
        emoji_status = f"{RUN_IS_FAILED}"
    elif status == "pending":
        emoji_status = f"{RUN_IS_PENDING}"
    elif status == "paused":
        emoji_status = f"{RUN_IS_PAUSED}"
    else:
        emoji_status = f"{RUN_IS_UNKNOWN}"

    return emoji_status


# --------------------------------------------------------
# Dataset CLI Constants
# --------------------------------------------------------
DATASET_NAME = NAME
DATASET_DESCRIPTION = DESCRIPTION
DATASET_PATH = PATH
DATASET_TAGS = TAGS
DATASET_ID = ID


# --------------------------------------------------------
# Status CLI Constants
# --------------------------------------------------------
STATUS_DISKSIZE = ":computer_disk:"
STATUS_EXPERIMENT = EXPERIMENT
STATUS_DATASET = DATASET
STATUS_RUN = RUN
STATUS_RUNNING = ":hourglass_not_done:"
