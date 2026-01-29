#!/usr/bin/env python3

"""
Copyright (C) 2022, Atgenomix Incorporated.

All Rights Reserved.

This program is an unpublished copyrighted work which is proprietary to
Atgenomix Incorporated and contains confidential information that is not to
be reproduced or disclosed to any other person or entity without prior
written consent from Atgenomix, Inc. in each and every instance.

Unauthorized reproduction of this program as well as unauthorized
preparation of derivative works based upon the program or distribution of
copies by sale, rental, lease or lending are violations of federal copyright
laws and state trade secret laws, punishable by civil and criminal penalties.
"""

# Standard Library
import signal
import sys

from nubia import Nubia, Options
from seqslab import auth, drs, organization, role, scr, trs, user, wes, workspace
from seqslab.plugin import SQLBPlugin


def signal_handler(sig, frame):
    msg = "\nCtrl-c was pressed. Do you really want to exit? [y/n] "
    sys.stderr.write(msg)
    ans = input()

    if ans == "y":
        print("")
        exit(1)
    else:
        print("", end="\r", flush=True)
        print(" " * len(msg), end="", flush=True)  # clear the printed line
        print("    ", end="\r", flush=True)


def main():
    signal.signal(signal.SIGINT, signal_handler)
    plugin = SQLBPlugin()
    shell = Nubia(
        name="seqslab-cli",
        command_pkgs=[auth, drs, wes, trs, workspace, user, role, organization, scr],
        plugin=plugin,
        options=Options(
            persistent_history=False, auto_execute_single_suggestions=False
        ),
    )
    sys.exit(shell.run())


if __name__ == "__main__":
    main()
