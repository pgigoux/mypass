# mypass
Password manager based on sqlite3, json and cryptography

# Installation

The program was written to run with Python 3.10 in a conda environment:

> conda create -n myp python=3.10<br>
> conda install cryptography<br>
> conda install pytest

# Running the program

Run the program as follows:

> conda activate myp<br>
> export XYZY_PLUGH='some_salt'<br>
> python $HOME/PycharmProjects/mypass/mypass.py<br>

The environment variable XYZY_PLUGH must contain the encryption salt. A default value is used if not defined.

# Tests

Run tests using: 

> python -m pytest .
