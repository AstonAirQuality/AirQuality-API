import os
import subprocess

# original pip commands
# pip install -t ../lib -r requirement.txt --platform manylinux2014_x86_64 --python-version 3.9  --implementation cp --abi cp39 --only-binary :all:
# pip install -t ../lib GeoAlchemy==0.7.2 GeoAlchemy2==0.12.5

## geopands windows install
# pip install pipwin
# pipwin install gdal
# pipwin install fiona
# pip install geopandas


def main():

    path_to_save = os.getcwd() + "/deployment/lib"
    requirements_file_path = os.getcwd() + "/deployment/requirements.txt"

    commands = [
        "python -m pip install -t {path_to_save} -r {requirements_file_path} --platform manylinux2014_x86_64 --python-version 3.9  --implementation cp --abi cp39 --only-binary :all:".format(
            path_to_save=path_to_save, requirements_file_path=requirements_file_path
        ),
        "python -m pip install -t {path_to_save} GeoAlchemy==0.7.2 GeoAlchemy2==0.12.5".format(path_to_save=path_to_save),
    ]

    for command in commands:
        subprocess.run(command, shell=True)


if __name__ == "__main__":
    main()
