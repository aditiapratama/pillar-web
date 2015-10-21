FROM ubuntu:14.04
MAINTAINER Francesco Siddi <francesco@blender.org>

RUN apt-get update && apt-get install -y \
python \
python-dev \
python-pip \
zlib1g-dev \
libjpeg-dev \
nano \
python-crypto \
python-openssl \
libssl-dev \
libffi-dev

RUN mkdir -p /data/git/pillar-web \
&& mkdir -p /data/git/pillar-python-sdk \
&& mkdir -p /data/storage/shared \
&& mkdir -p /data/storage/pillar-web/uploads \
&& mkdir -p /data/storage/pillar-web/storage

RUN pip install virtualenv \
&& virtualenv /data/venv

ENV PIP_PACKAGES_VERSION 1
ADD requirements.txt /requirements.txt

RUN . /data/venv/bin/activate \
&& pip install -r /requirements.txt

RUN ln -s /data/git/pillar-python-sdk/pillarsdk /data/venv/lib/python2.7/site-packages/pillarsdk

VOLUME /data/git/pillar-web
VOLUME /data/git/pillar-python-sdk
VOLUME /data/storage/shared
VOLUME /data/storage/pillar-web/uploads
VOLUME /data/storage/pillar-web/storage

EXPOSE 5001

ENV BUILD_VERSION 1

ADD runserver.sh /runserver.sh

ENTRYPOINT ["bash", "/runserver.sh"]
