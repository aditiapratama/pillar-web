FROM ubuntu:14.04
MAINTAINER Francesco Siddi <francesco@blender.org>

RUN apt-get update && apt-get install -y \
python \
python-dev \
python-pip \
zlib1g-dev \
libjpeg-dev \
nano \
vim \
apache2-mpm-event \
libapache2-mod-wsgi \
python-crypto \
python-openssl \
libssl-dev \
libffi-dev

RUN mkdir -p /data/git/pillar-web \
&& mkdir -p /data/git/pillar-python-sdk \
&& mkdir -p /data/storage/shared \
&& mkdir -p /data/storage/pillar-web/uploads \
&& mkdir -p /data/storage/pillar-web/storage

ENV APACHE_RUN_USER www-data
ENV APACHE_RUN_GROUP www-data
ENV APACHE_LOG_DIR /var/log/apache2
ENV APACHE_PID_FILE /var/run/apache2.pid
ENV APACHE_RUN_DIR /var/run/apache2
ENV APACHE_LOCK_DIR /var/lock/apache2

RUN mkdir -p $APACHE_RUN_DIR $APACHE_LOCK_DIR $APACHE_LOG_DIR

RUN pip install virtualenv \
&& virtualenv /data/venv

ENV PIP_PACKAGES_VERSION = 1
ADD requirements.txt /requirements.txt

RUN . /data/venv/bin/activate \
&& pip install -r /requirements.txt

RUN ln -s /data/git/pillar-python-sdk/pillarsdk /data/venv/lib/python2.7/site-packages/pillarsdk

ADD comodo.crt /usr/share/ca-certificates/
RUN echo comodo.crt >> /etc/ca-certificates.conf \
&& update-ca-certificates

ENV REQUESTS_CA_BUNDLE /etc/ssl/certs/comodo.pem

VOLUME /data/git/pillar-web
VOLUME /data/git/pillar-python-sdk
VOLUME /data/storage/shared
VOLUME /data/storage/pillar-web/uploads
VOLUME /data/storage/pillar-web/storage

EXPOSE 80

ADD 000-default.conf /etc/apache2/sites-available/000-default.conf

CMD ["/usr/sbin/apache2", "-D", "FOREGROUND"]
