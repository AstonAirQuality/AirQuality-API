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