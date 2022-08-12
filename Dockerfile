FROM python:3.9

ADD . /code
RUN cd /code && python -m pip install .
RUN rm -r /code

RUN mkdir -p /usr/local/var/ipsportal-instance && chmod 777 /usr/local/var/ipsportal-instance

CMD ["gunicorn", "-w", "16", "-b", "0.0.0.0:8080", "ipsportal:create_app()"]

ADD docker-entrypoint.sh /bin/docker-entrypoint.sh
RUN chmod +x /bin/docker-entrypoint.sh
ENTRYPOINT ["/bin/docker-entrypoint.sh"]
