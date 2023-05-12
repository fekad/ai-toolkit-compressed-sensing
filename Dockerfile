ARG BUILDER_BASE_IMAGE=jupyter/tensorflow-notebook:2022-06-27
FROM $BUILDER_BASE_IMAGE

# ================================================================================
# Linux applications and libraries
# ================================================================================

USER root

# RUN apt-get update --yes \
#  && apt-get install --yes --quiet --no-install-recommends \
#     build-essential g++ gfortran cmake git \
#  && apt-get clean \
#  && rm -rf /var/lib/apt/lists/*


RUN mamba install --quiet --yes \
    'numpy' \
    'pandas' \
    'scipy' \
    'seaborn' \
    'scikit-learn' \
 && mamba clean --all -f -y \
 && fix-permissions "${CONDA_DIR}" \
 && fix-permissions "/home/${NB_USER}"

# RUN pip install --no-cache-dir astropy

# ================================================================================
# Testing
# ================================================================================

# RUN pytest test

# ================================================================================

# ================================================================================

# USER ${NB_UID}

WORKDIR /home/${NB_USER}

COPY --chown=${NB_UID}:${NB_GID} notebook/assets notebook/compressed_sensing.ipynb ./






# Copy all the notebooks of the tutorials
ARG TUTORIALS_HOME=$HOME/tutorials

WORKDIR $TUTORIALS_HOME

COPY tutorials/*/*.ipynb ./

# Copy images or other assets may required by the tutorials
COPY tutorials/*/assets/*  ./

# Copy data may be required by the tutorials
COPY tutorials/*/data/* ./

# RUN jupyter-trust -y *.ipynb

# Fix permissions
RUN fix-permissions $TUTORIALS_HOME

# ================================================================================
# Install all of the package dependencies of the tutorials
# ================================================================================

RUN pip install ./analytics-compressed-sensing


