# Database migrations
Running migrations can fail due to the use of spatial fields in the database. This is because the geoalchemy package is not compatible with the alembic package.
To run a migration you must follow the below steps.

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
