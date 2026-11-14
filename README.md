## SETUP INSTRUCTIONS
You will need to install our forked version of qbepy. The pip command below will do this:

```bash
pip install -e qbepy-fork
```

The command must be re-ran whenever changes are made to qbepy. It is recommended that you create a Python virtual environment to avoid installing qbepy-fork globally. If you do so, please name your venv "py-venv". It is listed on the .gitignore to avoid commiting the virtual environment.

Please also have clang available on your path. It is necessary for the assembler and linking stage.

