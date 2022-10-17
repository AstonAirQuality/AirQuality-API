# AirQuality-API
Fast API project to fetch/scrape data from Aston's air quality sensors

# Tutorial

## Running Test suite
cd app
python -m coverage run -m unittest discover -s testing -p 'test_*.py'
OR WITHOUT COVEREAGE
python -m unittest discover -s testing -p 'test_*.py'
https://www.pythontutorial.net/python-unit-testing/python-unittest-coverage/

## deployment
https://adem.sh/blog/tutorial-fastapi-aws-lambda-serverless


## setup python virtual env
-   python -m venv env
-   python.exe -m pip install --upgrade pip

## activate env
-   cd env/scripts && activate && cd..\..
-   pip install -r requirements.txt


## gcp env 
pip install fastapi fastapi-sqlalchemy pydantic alembic psycopg2-binary uvicorn python-dotenv geoalchemy geoalchemy2 shapely pandas requests sentry-sdk mangum black PyJWT cryptography

## aws env
-   pip install fastapi fastapi-sqlalchemy pydantic alembic psycopg2-binary uvicorn python-dotenv geoalchemy geoalchemy2 shapely pandas requests sentry-sdk mangum black 

## heroku celery env
-   pip install fastapi fastapi-sqlalchemy celery redis pydantic alembic psycopg2-binary uvicorn python-dotenv geoalchemy geoalchemy2 shapely pandas requests sentry-sdk black 



## save dependacies
pip freeze > requirements.txt

## uninstall dependancies
pip uninstall -y -r requirements.txt 

# Docker commands - test enviornment
docker-compose build
docker-compose up

## run migration
- https://gist.github.com/utek/6163250
- https://geoalchemy-2.readthedocs.io/en/latest/alembic.html

docker-compose exec app alembic revision --autogenerate -m "New Migration"
docker-compose exec app alembic upgrade head

### Check migration file
- remove the create_index statement for spatial fields in the upgrade() function.
- remove the drop_index statement for spatial fields  in the downgrade() function.


## JS
https://arthur-e.github.io/Wicket/sandbox-gmaps3.html


# SPATIAL QUERY 
https://www.youtube.com/watch?v=siAjDNLMdKA
https://github.com/GeospatialProgramming/PostGIS/blob/main/GeoAlchemy2/GeoAlchemy2.ipynb

# https://pydantic-docs.helpmanual.io/usage/validators/
# links
- error handling: https://stackoverflow.com/questions/11587223/how-to-handle-assertionerror-in-python-and-find-out-which-line-or-statement-it-o
https://betterprogramming.pub/python-celery-best-practices-ae182730bb81
https://blog.frank-mich.com/creating-a-pydantic-model-for-gis-polygons/

