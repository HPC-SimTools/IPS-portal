FROM ubuntu:20.04

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

RUN \
    apt-get update              &&  \
    apt-get upgrade --yes       &&  \
    apt-get install --yes           \
    python3-flask                   \
    python3-pip                     \
    python3-pymongo                 \
    python3-waitress

ADD . /code
RUN cd /code && python3 -m pip install .
RUN rm -r /code

RUN mkdir -p /usr/var/ipsportal-instance && chmod 777 /usr/var/ipsportal-instance

CMD ["waitress-serve", "--call", "ipsportal:create_app"]

ADD docker-entrypoint.sh /bin/docker-entrypoint.sh
RUN chmod +x /bin/docker-entrypoint.sh
ENTRYPOINT ["/bin/docker-entrypoint.sh"]
