#!/usr/bin/env python
import shlex
import subprocess
import sys

if __name__ == "__main__":
    args = sys.argv[1:]
    extras = ["test"]
    if "--with-extras" in args:
        extras.append("kaplan-meier")
        args.remove("--with-extras")

    if "--no-deps" not in args:
        pip_install_cmd = [
            "pip",
            "install",
            "--no-cache-dir",
            "--disable-pip-version-check",
            "--no-python-version-warning",
            *args,
        ]
        if extras:
            pip_install_cmd.append(f".[{','.join(extras)}]")
        else:
            pip_install_cmd.append(f".")
        print("Running: ", shlex.join(pip_install_cmd))
        subprocess.run(pip_install_cmd, check=True)
    else:
        pip_install_cmd = ["pip", "install", "--no-deps", "."]
        print("Running: ", shlex.join(pip_install_cmd))
        subprocess.run(pip_install_cmd, check=True)
