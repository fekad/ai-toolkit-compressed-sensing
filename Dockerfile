ARG BUILDER_BASE_IMAGE=quay.io/jupyter/scipy-notebook:python-3.13
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
    pybind11-dev \
    openmpi-bin \
    libopenmpi-dev \
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
    'setuptools' \
    'bokeh' \
    'plotly'\
    'matplotlib' \
    'anywidget' \
    'colorcet' \
    'ase' \
    'selenium' \
    'nglview' \
 && mamba clean --all -f -y \
 && fix-permissions "${CONDA_DIR}" \
 && fix-permissions "/home/${NB_USER}"

RUN pip install --no-cache-dir \
    'pysr' \
    'ffx' \
    'jupyter_jsmol==2021.3.0'

# ================================================================================
#  SISSO++
# ================================================================================

USER ${NB_UID}
WORKDIR /opt/sissopp

COPY --chown=${NB_UID}:${NB_GID} 3rdparty/sissopp .

# CXX=$CXX_COMPILER CC=$C_COMPILER CXXFLAGS=$CXX_FLAGS -j ${N_PROCS}
RUN ./build_third_party.bash

RUN mkdir build && cd build \
 && cmake -C ../cmake/toolchains/gnu_param_py.cmake ../ \
 && make \
 && make install


# ================================================================================
# Setup the user
# ================================================================================

USER ${NB_UID}
WORKDIR /home/${NB_USER}


# ================================================================================
# Julia
# ================================================================================

RUN wget -O install.sh https://install.julialang.org \
 && chmod +x install.sh \
 && ./install.sh -y \
 && rm install.sh

ENV PATH="$PATH:/home/${NB_USER}/.juliaup/bin/"


# ================================================================================
# Install pySR Julia files
# ================================================================================

RUN python3 -c 'import pysr; pysr.install()'


# ================================================================================
# Copy the Data over
# ================================================================================

COPY --chown=${NB_UID}:${NB_GID} notebook/ .

