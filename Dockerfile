# Base image
FROM ubuntu:trusty

# Install dependencies via apt
RUN apt-get update && \
	apt-get install vim -y && \
    apt-get install python python-dev python-setuptools python-pip -y && \
    apt-get install uwsgi uwsgi-plugin-python -y && \
    apt-get install nginx supervisor -y

# Add and install python dependencies
ADD tweetbank/requirements.txt /home/tweetbank/requirements.txt
RUN pip install -r /home/tweetbank/requirements.txt

# Add application and utilities
ADD nginx /home/nginx
ADD uwsgi /home/uwsgi
ADD supervisor /home/supervisor
ADD tweetbank /home/tweetbank

# Prepare database
WORKDIR /home/tweetbank/
RUN cp db.sqlite3.master db.sqlite3

# Prepare static resources
RUN python manage.py collectstatic --clear --link --noinput

# Configure utilities
RUN echo "daemon off;" >> /etc/nginx/nginx.conf && \
    rm /etc/nginx/sites-enabled/default && \
    ln -s /home/nginx/website.conf /etc/nginx/sites-enabled/ && \
    mkdir -p /var/log/uwsgi && \
    mkdir -p /var/run/uwsgi && \
    ln -s /home/supervisor/website.conf /etc/supervisor/conf.d/
    
# Initialize supervisord
CMD ["supervisord", "-n"]