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
    libboost-mpi-dev libboost-serialization-dev libboost-system-dev libboost-filesystem-dev \
    libgtest-dev \
    coinor-clp coinor-libclp-dev \
    libnlopt-dev \
    pybind11-dev \
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
    'colorcet' \
    'jupyter_jsmol==2021.3.0' \
    'ase' \
    'pysr' \
    'ffx' \
    'selenium' \
    'tables' \
 && mamba clean --all -f -y \
 && fix-permissions "${CONDA_DIR}" \
 && fix-permissions "/home/${NB_USER}"

# ================================================================================
#  SISSO++
# ================================================================================

WORKDIR /opt/sissopp

COPY 3rdparty/sissopp .

# CXX=$CXX_COMPILER CC=$C_COMPILER CXXFLAGS=$CXX_FLAGS -j ${N_PROCS}
RUN ./build_third_party.bash

RUN mkdir build && cd build \
 && cmake -C ../cmake/toolchains/gnu_param_py.cmake -DEXTERNAL_BOOST=ON ../ \
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
 && ./install.sh -y

# ================================================================================
# Copy the Data over
# ================================================================================
ENV PATH="$PATH:/home/${NB_USER}/.juliaup/bin/"
# COPY --chown=${NB_UID}:${NB_GID} . .

COPY --chown=${NB_UID}:${NB_GID} notebook/ .

# ================================================================================
# Install all needed Python Packages
# ================================================================================
# RUN pip install -e .

# ================================================================================
# Install plotly widget for jupyter lab
# ================================================================================
# RUN jupyter labextension install plotlywidget

# ================================================================================
# Install pySR Julia files
# ================================================================================
RUN python3 -c 'import pysr; pysr.install()'

