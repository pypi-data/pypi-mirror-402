#!/bin/bash
#

# +----------------------+
# | Necessary Parameters |
# +----------------------+
# File Systems
PETSC_NAME="git.petsc"

# Lib Path & Compiler
INSTALL_PATH="${PWD}/install"
MPIEXEC="mpiexec"

MPIFC="mpifc"
export I_MPI_FC='ifx'

MPICC="mpicc"
export I_MPI_CC='icx'

MPICXX="mpicxx"
export I_MPI_CXX='icpx'

# +----------------------+
# | Init. Check          |
# +----------------------+
# Check if the Intel OneAPI is installed and enabled
if [ "$MKLROOT" == "" ]; then
    echo "[error] Intel OneAPI Libs (MKL&MPI for HPC) not loaded..."
    exit 1
fi

# +----------------------+
# | PETSc                |
# +----------------------+
# +......................+
# ' PETSc Git Pkg        '
# +......................+
echo "[do] Prepare the packages ..."

if [ -s downloads/${PETSC_NAME}.tar.gz ]; then 
    rm -rf install
    rm -rf ${PETSC_NAME}
    tar zxf downloads/${PETSC_NAME}.tar.gz --no-same-owner
else 
    echo "[error] 'downloads/${PETSC_NAME}.tar.gz' dose not exist..."
    echo "[error] Please check and re-download it..."
    exit 1
fi

# +......................+
# ' Compile!             '
# +......................+
cd ${PETSC_NAME}
unset MAKEFLAGS
./configure \
    --prefix=${INSTALL_PATH} \
    --with-cc=${MPICC} \
    --with-cxx=${MPICXX} \
    --with-fc=${MPIFC} \
    --with-mpiexec=${MPIEXEC} \
    --with-scalar-type=complex \
    --with-debugging=0 \
    --COPTFLAGS="-O3 -march=native" \
    --CXXOPTFLAGS="-O3 -march=native" \
    --FOPTFLAGS="-O3 -march=native"

# Make
make all
mkdir -p ${INSTALL_PATH}
make install
PETSC_DIR=${INSTALL_PATH} uv pip install ./src/binding/petsc4py
cd ..
echo "[done!]"
