# AirQuality-API
Fast API project to fetch/scrape data from Aston's air quality sensors

# Tutorial


## setup python virtual env
-   python -m venv env
-   python.exe -m pip install --upgrade pip
-   cd env/scripts && activate && cd..\..
-   pip install -r requirements.txt
-   pip install fastapi fastapi-sqlalchemy pydantic alembic psycopg2-binary uvicorn python-dotenv celery geoalchemy black shapely





## save dependacies
pip freeze > requirements.txt

# Docker commands 
docker-compose build
docker-compose up

## run migration
- https://gist.github.com/utek/6163250
- https://geoalchemy-2.readthedocs.io/en/latest/alembic.html

docker-compose exec app alembic revision --autogenerate -m "New Migration"
docker-compose exec app alembic upgrade head

### Check migration file
- remove the create_index statement in the upgrade() function.
- remove the drop_index statement in the downgrade() function.




# https://pydantic-docs.helpmanual.io/usage/validators/
# links
- error handling: https://stackoverflow.com/questions/11587223/how-to-handle-assertionerror-in-python-and-find-out-which-line-or-statement-it-o
https://betterprogramming.pub/python-celery-best-practices-ae182730bb81
https://blog.frank-mich.com/creating-a-pydantic-model-for-gis-polygons/

