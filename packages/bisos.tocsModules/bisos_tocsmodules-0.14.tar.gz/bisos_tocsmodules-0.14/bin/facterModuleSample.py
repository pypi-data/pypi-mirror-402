#   /bin/env loadAsHashTag.later


pyModuleType = "facter"

import getpass

def module_name(): return """sample"""

def module_version(): return "1.0"

def module_description():
    return """\
This is a sample facter module that does not do very much.
It just shows what the module interfaces are.
"""

def facterMain(
        *args,
        **kwargs,
):
    print(f"Running facterMain() As a LoadedAsCS:")
    print(f"args :: {args}")
    print(f"facterMain(KWArgs):")
    print(f"{kwargs}")

    for key, value in kwargs.items():
      print(key, "->", value)

    userName = getpass.getuser()


    print(f"{userName} using import getpass is in facterMain")


def module_params ():
    return [
        (
        "facterParName",  # parCliName
        "Facter Parameter Name",  # parName
        "Full Description of Parameter Comes Here", # parDescription
        "Int", # parDataType
        22, # parDefault
        [3,22,99] # parChoices
        ),
        (
        "doReport?",
        "doReport?",
        "Setting to No, Will disable reports generation. \
Report which nodes are compliant and which are not",
        "String",
        "Yes",
        ["Yes", "No"]
        ),
    ]
