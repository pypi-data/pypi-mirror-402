#!/bin/bash
#

BUFFER_SUBDIR=$1
declare -r SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

source ${SRC_DIR}/config.sh
source ${UV_MATTERGEN_ACT_SOURCE}

mattergen-generate ${STRUCTURE_POOL_BUFFER_PATH}/${BUFFER_SUBDIR} \
	--pretrained-name=${MATTERGEN_MODEL_NAME} \
	--properties_to_condition_on=${MATTERGEN_CONDITION} \
	--diffusion_guidance_factor=${MATTERGEN_DIFFUSION_FACTOR} \
	--batch_size=${MATTERGEN_BATCH_SIZE} \
	--num_batches=${MATTERGEN_NUM_BATCH} \
	--num_atoms_distribution=${MATTERGEN_NUM_ATOMS_DISTRIBUTION}
