# Use an official Node.js runtime as a parent image
FROM python:latest
# Set the working directory in the container
WORKDIR /usr/src/app

RUN apt update && apt upgrade -y
RUN apt install -y wget vim net-tools gcc make tar git unzip sysstat tree
RUN apt install -y python3 python3-pip python3-django

RUN pip3 install django djangorestframework django-cors-headers python-dotenv channels daphne pillow channels-redis asyncio
RUN pip3 install openai

# Copy your application code into the container
COPY ./backend .
# Expose a port your application will listen on
EXPOSE 8000

RUN python3 manage.py migrate

CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "realtime_commentary.asgi:application"]
#CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]