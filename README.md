# Schedule of notices of leases
Extracts schedule of notices of leases from pdf

### Running script
Uses `python3`

Create a virtual environment - Optional but recommended
```
    $ python -m venv venv
```

Install requirements.txt
```
    $ pip install -r requirements.txt
```

Run script using:
```
$ python script.py
```
The above command defaults to using the file `register.pdf` in the root directory and saves the result to `output.json` in the root directory.

To use a different file name or path, specify file name and/or path using `-f` or `--file` flag

```
$ python script.py -f <file path>
```

To save result to a different file or path, specify file name and/or path using `-o` or `--output` flag
```
$ python script.py -o <output file path>
```

Putting it together
```
$ python script.py -f <file path> -o <output file path>
```

For help, use `-h or --help` flag
```
$ python script.py -h
```
