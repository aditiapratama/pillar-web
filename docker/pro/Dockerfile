FROM ubuntu:14.04
MAINTAINER Francesco Siddi <francesco@blender.org>

RUN apt-get update && apt-get install -y \
python \
python-dev \
python-pip \
git \
zlib1g-dev \
libjpeg-dev \
nano \
vim \
apache2-mpm-event \
libapache2-mod-wsgi

RUN mkdir /data \
&& mkdir /data/dev \
&& mkdir /data/dev/pillar-web \
&& mkdir /data/dev/pillar-python-sdk \
&& mkdir /data/www \
&& mkdir /storage/shared \
&& mkdir /storage/pillar-web \
&& mkdir /storage/pillar-web/uploads \
&& mkdir /storage/pillar-web/storage

RUN git clone https://github.com/armadillica/pillar-web.git /data/www/pillar-web
#RUN git clone https://github.com/armadillica/pillar-python-sdk.git /data/www/

RUN pip install virtualenv \
&& virtualenv /data/venv

RUN . /data/venv/bin/activate \
&& pip install -r /data/www/pillar-web/requirements.txt

RUN ln -s /data/dev/pillar-python-sdk/pillarsdk /data/venv/lib/python2.7/site-packages/pillarsdk

VOLUME /data/dev/pillar-web
VOLUME /data/dev/pillar-python-sdk
VOLUME /storage/shared
VOLUME /storage/pillar-web/uploads
VOLUME /storage/pillar-web/storage

EXPOSE 5001

ADD 000-default.conf /etc/apache2/sites-available/000-default.conf

CMD ["/usr/sbin/apache2", "-D", "FOREGROUND"]
