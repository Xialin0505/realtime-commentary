FROM python:latest
WORKDIR /usr/src/app

# Install basic dependencies
RUN apt update && apt upgrade -y
RUN apt install -y python3 python3-pip git

# Install dependencies for Django
RUN pip3 install django djangorestframework django-cors-headers python-dotenv channels daphne
RUN pip3 install openai

# Copy your application code into the container
COPY ./backend .
# Expose a port your application will listen on
EXPOSE 8001

RUN python3 manage.py migrate

CMD ["daphne", "-b", "0.0.0.0", "-p", "8001", "realtime_commentary.asgi:application"]
