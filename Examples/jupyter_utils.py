"""
  ____       __                        __    __   __      _ __
 /_  / ___ _/ /  ___  ___ ___________ / /__ / /__/ /_____(_) /__
  / /_/ _ `/ _ \/ _ \/ -_) __/___/ -_) / -_)  '_/ __/ __/ /  '_/
 /___/\_,_/_//_/_//_/\__/_/      \__/_/\__/_/\_\\__/_/ /_/_/\_\

Copyright 2023 Zahner-Elektrik GmbH & Co. KG

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the Software
is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH
THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import json
import os
import pathlib

"""
This module contains internally required functions to automatically convert Jupyter notebooks into
pure python source code files. This way the user does not have to manually extract all the python
code from the jupyter code blocks.

Also a function has been implemented to detect if the source code is executed with python or in a
jupyter environment.
"""


def notebookCodeToPython(jupyterNotebookName):
    """Convert jupyter-notebook to python.

    This function extracts all code lines from a jupyter notebook and saves them as a file.
    With the standard jupyter export the whole documentation is inserted as a comment, but this is
    not desired.

    The code is then saved to a .py file of equal name.

    :param jupyterNotebookName: The notebook file name.
    """
    notebookText = ""
    with open(jupyterNotebookName, "r", encoding="utf-8") as f:
        notebookJson = json.load(f)
        for cell in notebookJson["cells"]:
            if "code" in cell["cell_type"]:
                for line in cell["source"]:
                    notebookText += line.rstrip("\n") + "\n"
                notebookText += "\n"

    jupyterName = jupyterNotebookName.replace("ipynb", "py")
    with open(jupyterName, "wb") as f:
        f.write(notebookText.encode(encoding="UTF-8"))

    os.system(f"python -m black {jupyterName}")
    return


def executionInNotebook():
    """Check if the code is executed in jupyter enviroment.

    This function checks if the execution of the code is done in python or in jupyter.
    The recognition is done via IPython and Python, it was only tested that it works on the
    development system with normal Python and the notebooks. It may be that an IPython environment
    is also recognised as a notebook.

    **This function is only needed for automation. The user does not need to use it.**

    :returns: True if the execution takes place in the jupyter enviroment.
    :rtype: bool
    """
    retval = False
    try:
        shell = get_ipython().__class__.__name__
        if "ZMQInteractiveShell" in shell:
            retval = True
    except NameError:
        pass

    return retval


if __name__ == "__main__":

    notebooks = [
        str(file)
        for file in list(
            pathlib.Path(os.path.dirname(os.path.realpath(__file__))).rglob("*.ipynb")
        )
        if "checkpoint" not in str(file)
    ]

    for notebook in notebooks:
        print(notebook)
        notebookCodeToPython(notebook)

    print("finish")
