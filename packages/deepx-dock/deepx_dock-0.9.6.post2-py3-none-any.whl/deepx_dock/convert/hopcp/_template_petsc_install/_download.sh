#!/bin/bash
#

# +----------------------------------+
# |          Init. Check             |
# +----------------------------------+
if [ ! -d "downloads" ]; then
    echo "[do] mkdir downloads"
    mkdir downloads
fi

# +----------------------------------+
# |         Sub Functions            |
# +----------------------------------+
download_git() {
    GIT_URL=$1
    GIT_BARNCH=$2
    GIT_FOLDER=$3
    TGZ=${GIT_FOLDER}.tar.gz
    # Check if the git exist in the package folder
    if [ -e "${TGZ}" ]; then
        echo "[skip] The '${TGZ}' has been downloaded..."
        return
    fi
    # Download the git
    echo "[do] git clone -b ${GIT_BARNCH} ${GIT_URL} ${GIT_FOLDER}"
    git clone -b ${GIT_BARNCH} ${GIT_URL} ${GIT_FOLDER}
    # Timeout info 
    if [ $? -eq 124 ]; then
        echo "[error] Download failed, check your connection to GitHub."
        echo "[error] Skip the '${GIT_FOLDER}' download..."
        return
    fi
    # Tarball
    tar zcf ${TGZ} ${GIT_FOLDER}
    rm -rf ${GIT_FOLDER}
}

# +----------------------------------+
# |          Download Libs           |
# +----------------------------------+
cd downloads
PETSC_GIT="https://gitlab.com/petsc/petsc.git"
PETSC_NAME="git.petsc"
download_git ${PETSC_GIT} release ${PETSC_NAME}
cd ..
