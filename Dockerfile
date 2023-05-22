ARG BUILDER_BASE_IMAGE=jupyter/scipy-notebook:python-3.9
FROM $BUILDER_BASE_IMAGE as builder

# Julia installation
# Default values can be overridden at build time
# (ARGS are in lower case to distinguish them from ENV)
# Check https://julialang.org/downloads/
ARG julia_version="1.8.5"

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


# ================================================================================
#  SISSO++
# ================================================================================

USER ${NB_UID}

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

USER root
WORKDIR /app/3rdparty/sissopp

COPY 3rdparty/sissopp .

RUN mkdir build && cd build \
 && cmake -C ../cmake/toolchains/gnu_param_py.cmake \
    -DEXTERNAL_BOOST=OFF \
    -DCMAKE_INSTALL_PREFIX=/opt/sissopp \
    ../ \
 && make \
 && make install \
 && fix-permissions "/opt/sissopp" \
 && fix-permissions "${CONDA_DIR}" \
 && fix-permissions "/home/${NB_USER}"


# ================================================================================
# Julia
# ================================================================================

USER root

# Julia dependencies
# install Julia packages in /opt/julia instead of ${HOME}
ENV JULIA_DEPOT_PATH=/opt/julia \
    JULIA_PKGDIR=/opt/julia \
    JULIA_VERSION="${julia_version}"

WORKDIR /tmp

RUN set -x && \
    julia_arch=$(uname -m) && \
    julia_short_arch="${julia_arch}" && \
    if [ "${julia_short_arch}" == "x86_64" ]; then \
      julia_short_arch="x64"; \
    fi; \
    julia_installer="julia-${JULIA_VERSION}-linux-${julia_arch}.tar.gz" && \
    julia_major_minor=$(echo "${JULIA_VERSION}" | cut -d. -f 1,2) && \
    mkdir "/opt/julia-${JULIA_VERSION}" && \
    wget -q "https://julialang-s3.julialang.org/bin/linux/${julia_short_arch}/${julia_major_minor}/${julia_installer}" && \
    tar xzf "${julia_installer}" -C "/opt/julia-${JULIA_VERSION}" --strip-components=1 && \
    rm "${julia_installer}" && \
    ln -fs /opt/julia-*/bin/julia /usr/local/bin/julia

# Show Julia where conda libraries are \
RUN mkdir /etc/julia && \
    echo "push!(Libdl.DL_LOAD_PATH, \"${CONDA_DIR}/lib\")" >> /etc/julia/juliarc.jl && \
    # Create JULIA_PKGDIR \
    mkdir "${JULIA_PKGDIR}" && \
    chown "${NB_USER}" "${JULIA_PKGDIR}" && \
    fix-permissions "${JULIA_PKGDIR}"

USER ${NB_UID}

# Add Julia packages.
# Install IJulia as jovyan and then move the kernelspec out
# to the system share location. Avoids problems with runtime UID change not
# taking effect properly on the .local folder in the jovyan home dir.
RUN julia -e 'import Pkg; Pkg.update()' && \
    julia -e 'import Pkg; Pkg.add("PyCall")' && \
    julia -e 'using Pkg; pkg"add IJulia"; pkg"precompile"' && \
    # move kernelspec out of home \
    mv "${HOME}/.local/share/jupyter/kernels/julia"* "${CONDA_DIR}/share/jupyter/kernels/" && \
    chmod -R go+rx "${CONDA_DIR}/share/jupyter" && \
    rm -rf "${HOME}/.local" && \
    fix-permissions "${JULIA_PKGDIR}" "${CONDA_DIR}/share/jupyter"

# ================================================================================
# Install all needed Python Packages
# ================================================================================

USER ${NB_UID}

# Workaround to install ffx and it deppendencies except the deprecated sklearn package
RUN pip install --no-cache-dir contextlib2 \
 && pip install --no-cache-dir --no-deps ffx \
 && fix-permissions "${CONDA_DIR}" \
 && fix-permissions "/home/${NB_USER}"


# ================================================================================
# Install all needed Python Packages
# ================================================================================

USER ${NB_UID}
WORKDIR /tmp/app

COPY --chown=${NB_UID}:${NB_GID} src ./src
COPY --chown=${NB_UID}:${NB_GID} pyproject.toml README.md ./

# Workaround to install ffx and it deppendencies except the deprecated sklearn package
RUN pip install --no-cache-dir contextlib2 \
 && pip install --no-cache-dir --no-deps ffx \
 && fix-permissions "${CONDA_DIR}" \
 && fix-permissions "/home/${NB_USER}"

RUN --mount=source=.git,target=.git,type=bind \
     pip --no-cache-dir install . \
 && fix-permissions "${CONDA_DIR}" \
 && fix-permissions "/home/${NB_USER}"

# ================================================================================
# Setup the user
# ================================================================================

USER ${NB_UID}
WORKDIR "${HOME}"

COPY --chown=${NB_UID}:${NB_GID} notebook .

# ================================================================================
# Install pySR Julia files
# ================================================================================

RUN python -c 'import pysr; pysr.install("@/opt/julia/environments/v1.8/")'

ENV DOCKER_STACKS_JUPYTER_CMD="nbclassic"
