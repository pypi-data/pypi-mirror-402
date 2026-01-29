import json
from ._globals import config, config_file


def update_config(**kwargs: dict) -> None:
    """
    Update the configuration settings for the SMI index module.

    Inputs
    ======
    kwargs : dict
        Key-value pairs of configuration settings to update.

    Returns
    =======
    None
    """

    # Update the in-memory config dictionary
    for key, value in kwargs.items():
        config[key] = value

    # Write the updated config back to the JSON file
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)


def set_username() -> str:
    """
    Prompt the user to input their SuperMAG username and update the config.

    Returns
    =======
    None
    """
    print("Please visit https://supermag.jhuapl.edu/mag/ to create an account if you haven't already and obtain a username")
    input("Press Enter to continue...")

    username = input("Enter your SuperMAG username: ")
    update_config(username=username)

    return username
