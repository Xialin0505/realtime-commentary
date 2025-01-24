# Use an official Node.js runtime as a parent image
FROM python:latest
# Set the working directory in the container
WORKDIR /usr/src/app

RUN apt update && apt upgrade -y
RUN apt install -y wget vim net-tools gcc make tar git unzip sysstat tree
RUN apt install -y python3
RUN apt install -y python3-pip
RUN apt install -y git
RUN apt install -y python3-django

RUN pip3 install django djangorestframework django-cors-headers python-dotenv channels daphne 
RUN pip3 install openai

# Copy your application code into the container
COPY ./backend .
# Expose a port your application will listen on
EXPOSE 8000

RUN python3 manage.py migrate

CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]