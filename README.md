# AirQuality-API
Severless AWS lambda & Fast API project to fetch/scrape data from Aston's air quality sensors into a postgres database.
Manage sensors and query sensor data

API available on: https://rn3rb93aq5.execute-api.eu-west-2.amazonaws.com/prod/ (open)  

# Setting up Docker

## Installation (for windows)
install Docker desktop - https://docs.docker.com/desktop/install/windows-install/

## Building containers from docker compose 
**Ensure you are in the root project directory and the env file is in the project root directory**
### Building development container stack
run the command ```docker-compose up```
### Building test container stack
run the command  ```docker-compose -f docker-compose-testenv.yml -p test up -d```
delete test container ```docker-compose -f docker-compose-testenv.yml -p test down --volumes```
## Exiting Docker
if using docker desktop you can simply click stop running containers for "app"
if using docker was initialised using a CMD then press **Ctrl + C** or press twice to force close  **Ctrl + C , Ctrl + C**

# Setting up the python enviornment (Windows setup)
install python 3.9.6 or the latest version https://www.python.org/downloads/
cd into the root project directory

Run the following commands to create a virtual python enviornment for this project, and upgrade pip
- ```python -m venv env```
- ```python.exe -m pip install --upgrade pip```

## Activating the virtual python enviornment
```cd env/scripts && activate && cd..\..```

### If the above command fails then try it separately 
- ```cd env/scripts```
- ```activate```
- ```cd..\..```

## Installing project dependancies
```pip install -r requirements.txt```

## Uninstalling project dependancies (forced)
```pip uninstall -y -r requirements.txt```

## Save project dependancies
```pip freeze > requirements.txt```

# Testing
from the project root directory run the commands ```cd app```

Run tests without coverage ```python -m unittest discover -s testing -p test_*.py```

Run tests with coverage ```python -m coverage run -m unittest discover -s testing -p test_*.py```

View coverage report ```python -m coverage report --omit="*/testing*" ```

export coverage in html ```python -m coverage html --omit="*/testing*```  

for more information see
- https://www.pythontutorial.net/python-unit-testing/python-unittest-coverage/

## Using test suites and generating HTML reports
amend the code in the HTMLTestRunner package, to do this see the link: https://stackoverflow.com/questions/71858651/attributeerror-htmltestresult-object-has-no-attribute-count-relevant-tb-lev 

Then you can just run the TestRunner scripts which are lcoated in the testing/suites directory as python modules

# Database migrations
Running migrations is a little buggy because of the geoalchemy package. A few extra steps need to be taken to successfully run a migration

## Running a migration
To begin run the docker containers.

To create a new migration use the below command. ```docker-compose exec app alembic revision --autogenerate -m "New Migration"```.
<br>You may use a custom migration name instead of "New Migration"


To run the migration you can use this command. ```docker-compose exec app alembic upgrade head``` 
<br> **You should always check your migration file before running it** 


## Checking a migration file

### Finding the migration file
from the project root directroy go into the alembic/versions
your new migration will be located here. 

### Checking the migration file
Errors can occur when inserting or changing columns with spatial fields. 

for more information see: 
- https://gist.github.com/utek/6163250
- https://geoalchemy-2.readthedocs.io/en/latest/alembic.html

You must follow the below steps if spatial fields exist in the migration file: 

- remove the create_index statement for spatial fields in the upgrade() function.
- remove the drop_index statement for spatial fields  in the downgrade() function.


# Deployment

## Creating a zip file of the api
- install dependancies with the command ```python deployment/scripts/installDependancies.py```
- zip the project with the command ```python deployment/scripts/zipProject.py```

## Uploading the file to aws
- check the unzipped file size does not exceed 250mb. (zip file should not be larger than 75mb). If it is then consider setting up a lambda image deployment 
- login to aws and navigate to s3 bucket
- upload the new app.zip file and copy the url path
- navigate to lambda and click the code tab, select upload from Amazon s3 location and poste the url path
- once the uplaod is complete navigate the api's base url and check if it works correctly.