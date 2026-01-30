#!/usr/bin/env bash
set -euo pipefail

mkdir -p "${WORKSPACE}"
echo "AGENT_DIR=${AGENT_DIR}" > "${WORKSPACE}/bundle_env.txt"
echo "TASK_DIR=${TASK_DIR}" >> "${WORKSPACE}/bundle_env.txt"
echo "WORKSPACE=${WORKSPACE}" >> "${WORKSPACE}/bundle_env.txt"
echo "RUN_ID=${RUN_ID}" >> "${WORKSPACE}/bundle_env.txt"
echo "TASK_ID=${TASK_ID}" >> "${WORKSPACE}/bundle_env.txt"
echo "EXPERIMENT_ID=${EXPERIMENT_ID}" >> "${WORKSPACE}/bundle_env.txt"
echo "BACKEND=${BACKEND}" >> "${WORKSPACE}/bundle_env.txt"
