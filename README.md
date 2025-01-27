## Realtime Commentary

### Setup
1. clone the git repo
2. nagivate to `backend/llmserver` and create a file named `.env`
3. inside the `.env` file, insert a line `OPENAI_API_KEY = ""` and copy the OPENAI API key into the quote

### Run the backend server

#### WSGI Server (HTTP)
```
cd backend
daphne -b 0.0.0.0 -p 8000 realtime_commentary.asgi:application # ASGI Server (Websocket)
```

open the url `http://127.0.0.1:8000/generate/?sequence=#` will generate the streaming chat content

### Run the frontend
```
cd frontend
npm run start
```

open the url `http://127.0.0.1:3000` will show the react page

### Run within container
to setup the docker container
`bash run.sh up`

to bring down and clean up the docker container
`bash run.sh down`

to rebuild the docker container
`docker-compose build`

the project directory is mounted inside the `/mnt` folder for development
the porject directory is copied inside the `usr/src/app` folder as the production