#!/bin/bash
#

BUFFER_SUBDIR=$1
declare -r SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

source ${SRC_DIR}/config.sh
source ${UV_CHGNET_ACT_SOURCE}

python ${SRC_DIR}/_relax.py \
    --buffer ${STRUCTURE_POOL_BUFFER_PATH}/${BUFFER_SUBDIR} \
    --origin ${STRUCTURE_POOL_ORIGIN_PATH} \
    --relaxed ${STRUCTURE_POOL_RELAXED_PATH} \
    --error ${STRUCTURE_POOL_ERROR_PATH} \
    --F_max ${CHGNET_F_MAX} \
    --N_max ${CHGNET_N_MAX} \
    ${CHGNET_EXTRA_OPTIONS}
