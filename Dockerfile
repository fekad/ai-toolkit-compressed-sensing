ARG BUILDER_BASE_IMAGE=jupyter/scipy-notebook:python-3.9
FROM $BUILDER_BASE_IMAGE

# Read more: https://sissopp_developers.gitlab.io/sissopp/quick_start/Installation.html

# ================================================================================
# Linux applications and libraries
# ================================================================================

USER root

RUN apt-get update \
 && apt-get install --yes --quiet --no-install-recommends \
    build-essential g++ gfortran cmake git \
    liblapack-dev libblas-dev \
    zlib1g-dev \
    libboost-mpi-dev libboost-serialization-dev libboost-system-dev libboost-filesystem-dev \
    libgtest-dev \
    coinor-clp coinor-libclp-dev \
    # libnlopt-dev \
    openssh-client \
    dvipng \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

RUN mamba install --quiet --yes \
    'numpy' \
    'pandas' \
    'scipy' \
    'seaborn' \
    'scikit-learn' \
    'toml' \
    'pytest' \
 && mamba clean --all -f -y \
 && fix-permissions "${CONDA_DIR}" \
 && fix-permissions "/home/${NB_USER}"

# RUN pip install --no-cache-dir \
#     'jupyter-jsmol==2021.3.0'
#  && fix-permissions "${CONDA_DIR}" \
#  && fix-permissions "/home/${NB_USER}"


# ================================================================================
#  SISSO++
# ================================================================================

WORKDIR /opt/sissopp

COPY 3rdparty/sissopp .

RUN mkdir build && cd build \
 && cmake -C ../cmake/toolchains/gnu_param_py.cmake -DEXTERNAL_BOOST=ON ../ \
 && make \
 && make install



# ================================================================================
# Testing
# ================================================================================

# RUN pytest tests/pytest
# RUN cd build \
#  && cmake test

# RUN pytest test

# ================================================================================
#
# ================================================================================

USER ${NB_UID}
WORKDIR /home/${NB_USER}

# ================================================================================
# Julia
# ================================================================================
RUN wget -O install.sh https://install.julialang.org \
 && chmod +x install.sh \
 && ./install.sh -y

ENV PATH="$PATH:/home/jovyan/.juliaup/bin/"
COPY --chown=${NB_UID}:${NB_GID} . .
# COPY --chown=${NB_UID}:${NB_GID} notebook/assets notebook/compressed_sensing.ipynb ./


# Fix permissions
# RUN fix-permissions $TUTORIALS_HOME

# ================================================================================
# Install all of the package dependencies of the tutorials
# ================================================================================

RUN pip install -e .
RUN python3 -c 'import pysr; pysr.install()'
ENTRYPOINT jupyter notebook --ip 0.0.0.0 --no-browser --allow-root
