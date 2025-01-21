## Realtime Commentary

### Setup
clone the git repo

### Run the backend server
```
cd backend
python3 manage.py runserver "0.0.0.0:8000"
```

open the url `http://127.0.0.1:8000/generate/?sequence=#` will generate the streaming chat content

### Run the frontend


### Run within container
to setup the docker container
`bash run.sh up`

to bring down and clean up the docker container
`bash run.sh down`

to rebuild the docker container
`docker-compose build`

the project directory is mounted inside the `/mnt` folder