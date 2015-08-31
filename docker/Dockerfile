FROM debian
MAINTAINER Francesco Siddi <francesco@blender.org>

RUN apt-get update && apt-get install -y \
python \
python-dev \
python-pip \
git \
nano

RUN mkdir /data
RUN mkdir /data/www
RUN mkdir /data/www/pillar_web
RUN mkdir /data/www/pillar_web_dev

RUN git clone https://github.com/armadillica/pillar-web.git /data/www/pillar_web

RUN pip install virtualenv
RUN virtualenv /data/venv
RUN . /data/venv/bin/activate
RUN pip install -r /data/www/pillar_web/requirements.txt

VOLUME /data/www/pillar_web_dev

EXPOSE 5001

#ENTRYPOINT . /data/venv/bin/activate; \
#cd /data/www/pillar_dev; \
