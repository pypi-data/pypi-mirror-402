readonly UV_MATTERGEN_ACT_SOURCE="/home/deeph/py_env/mattergen/bin/activate"
readonly UV_CHGNET_ACT_SOURCE="/home/deeph/py_env/chgnet/bin/activate"

readonly STRUCTURE_POOL_BUFFER_PATH="POOL/BUFFER"
readonly STRUCTURE_POOL_ORIGIN_PATH="POOL/ORIGIN"
readonly STRUCTURE_POOL_RELAXED_PATH="POOL/RELAXED"
readonly STRUCTURE_POOL_ERROR_PATH="POOL/ERROR"

readonly MATTERGEN_MODEL_NAME="chemical_system"
readonly MATTERGEN_CONDITION='{"chemical_system":"B-**!La,Ce,Pr,Nd,Sm,Eu,Gd,Tb,Dy,Ho,Er,Tm,Yb,Lu"}'
readonly MATTERGEN_DIFFUSION_FACTOR=2.0
readonly MATTERGEN_BATCH_SIZE=32
readonly MATTERGEN_NUM_BATCH=512
readonly MATTERGEN_NUM_ATOMS_DISTRIBUTION="ALEX_MP_20"

readonly CHGNET_F_MAX=0.02
readonly CHGNET_N_MAX=500
readonly CHGNET_EXTRA_OPTIONS="--save_trajectory_info"
