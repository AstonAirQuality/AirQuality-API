
# Setting up EC2 instance.
1. Create an EC2 instance on AWS using either Ubuntu or Debian.
2. Create a key pair and download the .pem file.
3. Open terminal and navigate to the directory where the .pem file is located.
4. Change the permission of the .pem file using the command:
   ```bash
   chmod 400 your-key-pair.pem
   ```
5. Connect to the EC2 instance using SSH:
   ```bash
    ssh -i "your-key-pair.pem" ubuntu@your-ec2-public-dns
    ```
6. Update the package lists:
    ```bash
    sudo apt update
    ```
7. Install postgres and postgis
    ```bash
    sudo apt install postgresql postgresql-contrib postgis
    ```
8. Switch to the postgres user:
    ```bash
    sudo -i -u postgres
    ```
9. Access the PostgreSQL prompt:
    ```bash
    psql
    ```
10. Create a new database:
    ```sql
    CREATE DATABASE airqualitydb;
    ```
11. Connect to the new database:
    ```sql
    \c airqualitydb;
    ```
12. Enable the PostGIS extension:
    ```sql
    CREATE EXTENSION postgis;
    ```
13. Exit the PostgreSQL prompt:
    ```sql
    \q
    ```
14. Exit the postgres user:
    ```
    exit
    ```
15. Allow remote connections to PostgreSQL:
    ```bash
    sudo nano /etc/postgresql/12/main/postgresql.conf
    ```
    - Find the line `#listen_addresses = 'localhost'` and change it to:
      ```
      listen_addresses = '*'
      ```
    - Save and exit the file (Ctrl + X, then Y, then Enter).
16. Configure client authentication:
    ```bash
    sudo nano /etc/postgresql/12/main/pg_hba.conf
    ```
    - Add the following line at the end of the file to allow remote connections:
      ```
      host    all             all

      ```
17. Restart PostgreSQL to apply the changes:
    ```bash
    sudo systemctl restart postgresql
    ```

18. Change the password for the postgres user:
    ```bash
    sudo -i -u postgres
    psql
    ALTER USER postgres PASSWORD 'yourpassword';
    \q
    exit
    ```
19. Update your security group settings on AWS to allow inbound traffic on port 5432 (PostgreSQL default port) from your IP address or range.
20. Update your `.env` file in your application to point to the new EC2 PostgreSQL instance:
    ```
    DATABASE_URL=postgresql+psycopg2://postgres:yourpassword@your-ec2-public-dns:5432/airqualitydb
    ```
    Replace `yourpassword` with the password you set for the postgres user and `your-ec2-public-dns` with the public DNS of your EC2 instance.
21. Test the connection from your application to ensure everything is set up correctly (you can do this locally or from backend server by changing the .env for the db url).

# Transfer Data from RDS to EC2
1. SSH into your EC2 instance.
2. Dump the RDS database to a file using `pg_dump`:
   ```bash
   pg_dump -h aston-air-quality.cticfcf2ovks.eu-west-2.rds.amazonaws.com -p 5432 -U postgres -d airqualitydb > rds_dump.sql
   ```
   Replace `your-rds-endpoint`, `your-username`, and `your-database-name` with your RDS instance details.
3. Load the dump file into your EC2 PostgreSQL database:
   ```bash
   psql -h localhost -U postgres -d airqualitydb -f rds_dump.sql
   ```
    Replace `your-username` and `your-database-name` with your EC2 PostgreSQL details.
    - You will be prompted to enter the password for the postgres user.
4. Verify that the data has been transferred successfully by connecting to the EC2 PostgreSQL database and checking the tables.
    ```bash
    psql -h localhost -U postgres -d airqualitydb
    \dt
    ```
    - You should see a list of tables that were in your RDS database.
5. Update your application configuration to point to the new EC2 PostgreSQL instance if you haven't done so already.
    ```
    DATABASE_URL=postgresql+psycopg2://postgres:yourpassword@your-ec2-public-dns:5432/airqualitydb
    ```
    Replace `yourpassword` with the password you set for the postgres user and `your-ec2-public-dns` with the public DNS of your EC2 instance.
    - Test your application to ensure it can connect to the new database and that all data is accessible.

# Final Steps
1. Ensure that your EC2 instance is properly secured, including setting up firewalls and security groups to restrict access to only necessary IP addresses.
2. Create backups of the EC2 PostgreSQL database.

# Maintenance and Monitoring
1. Regularly back up your EC2 PostgreSQL database using `pg_dump` and store the backups securely.
2. Monitor the performance of your EC2 instance and PostgreSQL database using AWS CloudWatch and PostgreSQL monitoring tools.
3. Keep your EC2 instance and PostgreSQL software up to date with the latest security patches and updates.