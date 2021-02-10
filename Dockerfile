FROM ubuntu:20.04

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

RUN \
    apt-get update              &&  \
    apt-get upgrade --yes       &&  \
    apt-get install --yes           \
    python3-flask

ADD ipsportal /srv/ipsportal
ENV FLASK_APP=ipsportal
WORKDIR "/srv"
RUN ["flask", "init-db"]
CMD ["flask", "run", "--host=0.0.0.0"]
