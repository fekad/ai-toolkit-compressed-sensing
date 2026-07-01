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
    'ase' \
    'numpy' \
    'scipy' \
    'pandas' \
    'seaborn' \
    'scikit-learn' \
    'toml' \
    'bokeh' \
    'plotly'\
    'matplotlib' \
    'anywidget' \
    'nglview' \
 && mamba clean --all -f -y \
 && fix-permissions "${CONDA_DIR}" \
 && fix-permissions "/home/${NB_USER}"


# Fixing nglview package (https://github.com/nglviewer/nglview/issues/1172#issuecomment-4476260864)
RUN sed -i "s/__frontend_version__ = '4.0'/__frontend_version__ = '3.1.5'/"  "${CONDA_DIR}/lib/python3.13/site-packages/nglview/_frontend.py"


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
# Copy the Data over
# ================================================================================

COPY --chown=${NB_UID}:${NB_GID} notebook/ .




