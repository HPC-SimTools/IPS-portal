FROM continuumio/miniconda3

ADD . /code
RUN conda env update --name base --file /code/environment.yml

RUN cd /code && python3 -m pip install .
RUN rm -r /code

RUN mkdir -p /usr/var/ipsportal-instance && chmod 777 /usr/var/ipsportal-instance

CMD ["waitress-serve", "--call", "ipsportal:create_app"]

ADD docker-entrypoint.sh /bin/docker-entrypoint.sh
RUN chmod +x /bin/docker-entrypoint.sh
ENTRYPOINT ["/bin/docker-entrypoint.sh"]
