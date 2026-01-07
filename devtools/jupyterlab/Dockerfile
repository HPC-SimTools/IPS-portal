FROM quay.io/jupyter/base-notebook
# Add dependencies in environment we want to simulate
RUN pip install --no-cache-dir \
  adios2 \
  bokeh \
  ipywidgets
RUN mkdir -p /home/jovyan/work && chmod 777 /home/jovyan/work
