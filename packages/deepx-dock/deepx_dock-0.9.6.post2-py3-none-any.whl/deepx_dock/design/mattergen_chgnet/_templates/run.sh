#!/bin/bash
#

readonly BUFFER_SUBDIR="$1"
readonly RUN_SUBDIR="run/${BUFFER_SUBDIR}"
readonly SRC_DIR="$(cd $(dirname $(readlink -f ${BASH_SOURCE[0]})) >/dev/null 2>&1 && pwd)"

mkdir -p "${RUN_SUBDIR}"

# Parallel exec two command
echo "[do] Submitting the MatterGen task ${BUFFER_SUBDIR}..."
bash "${SRC_DIR}/_generate.sh" "${BUFFER_SUBDIR}" >> "${RUN_SUBDIR}/generate.log" 2>&1 &
generate_pid=$!
echo "[info] The generate task id are ${generate_pid}."

echo "[do] Submitting the CHGNet task ${BUFFER_SUBDIR}..."
bash "${SRC_DIR}/_relax.sh" "${BUFFER_SUBDIR}" >> "${RUN_SUBDIR}/relax.log" 2>&1 &
relax_pid=$!
echo "[info] The relax task id are ${relax_pid}."

echo "[wait] Waiting for the tasks to finish..."
echo "[info] The run log files are saved in dir: $(readlink -f ${RUN_SUBDIR})"

# wait for all tasks to finish
wait "${generate_pid}" "${relax_pid}" || {
    echo "ERROR: One or more tasks failed" >&2
    exit 1
}
