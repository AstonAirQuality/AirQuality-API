import os
from os import path
from zipfile import ZIP_DEFLATED, ZipFile

# TODO ignore coverage


def zip_directory(directory_path, isDependancy: bool):
    for folderName, subfolders, filenames in os.walk(directory_path):
        if folderName.endswith("__pycache__"):
            continue

        if isDependancy:
            if folderName.endswith("testing") or folderName.endswith("test_data") or folderName.endswith("test_api"):
                continue

        for filename in filenames:
            if isDependancy:
                if filename.endswith(".sql") or filename.endswith("Dockerfile") or filename.endswith(".env"):
                    continue

            # Create Complete Filepath of file in directory
            filePath = os.path.join(folderName, filename)
            # Add file to zip
            arcname = filePath.replace(directory_path, "")

            yield (filePath, arcname)


def main():

    # Check if file exists
    dependaciesPath = os.getcwd() + "/deployment/lib"

    if path.exists(dependaciesPath):

        with ZipFile("deployment/export/app.zip", "w", ZIP_DEFLATED) as zipFileObj:

            for (file, arcname) in zip_directory(dependaciesPath, False):
                zipFileObj.write(file, arcname=arcname)

        path_to_app = os.getcwd() + "/app"
        with ZipFile("deployment/export/app.zip", "a", ZIP_DEFLATED) as zipFileObj:

            for (file, arcname) in zip_directory(path_to_app, True):
                zipFileObj.write(file, arcname=arcname)

    else:
        print("Project dependancies not found. Please run installDependancies.py first.")


if __name__ == "__main__":
    main()
