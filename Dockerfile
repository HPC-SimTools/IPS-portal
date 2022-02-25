FROM continuumio/miniconda3

RUN conda install \
    flask=2.0 \
    pymongo=3.12 \
    waitress=2.0 \
    pip \
    plotly=5.1 \
    numpy=1.21

ADD . /code
RUN cd /code && python3 -m pip install .
RUN rm -r /code

RUN mkdir -p /usr/var/ipsportal-instance && chmod 777 /usr/var/ipsportal-instance

CMD ["waitress-serve", "--call", "ipsportal:create_app"]

ADD docker-entrypoint.sh /bin/docker-entrypoint.sh
RUN chmod +x /bin/docker-entrypoint.sh
ENTRYPOINT ["/bin/docker-entrypoint.sh"]
