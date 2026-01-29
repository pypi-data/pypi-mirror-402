FROM continuumio/miniconda3

# Install system dependencies
USER root
RUN apt-get update \
  && apt-get install -y build-essential git tree curl sudo vim wget \
  && apt-get clean \
  && apt-get purge 

# Install conda env
COPY environment.yml /tmp/env.yaml

# Install mamba in the base environment
RUN conda config --add channels conda-forge \
  && conda config --add channels bioconda \
  && conda config --set channel_priority false 

# Create the dev environment using mamba
RUN conda install -y -n base -c conda-forge mamba \
  && mamba env create -n dev -f /tmp/env.yaml \
  && conda clean --all --yes \
  && rm -f /tmp/env.yaml
