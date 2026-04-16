FROM quay.io/jupyter/base-notebook
# Add dependencies in environment we want to simulate
RUN pip install --no-cache-dir \
  adios2 \
  bokeh \
  ipywidgets
# make sure "work" directory has setgid
RUN mkdir -p /home/jovyan/work && chmod 2770 /home/jovyan/work
COPY docker-cmd.sh /usr/local/bin/docker-cmd.sh
# base image already has an entrypoint which would be unwise to override, so use a CMD instead
CMD [ "/usr/local/bin/docker-cmd.sh" ]
