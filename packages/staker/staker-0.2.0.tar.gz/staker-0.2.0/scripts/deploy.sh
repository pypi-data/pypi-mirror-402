#!/bin/bash
#
# Deploy CloudFormation stack for Ethereum staking infrastructure.
# Usage: DEPLOY_ENV=prod ./scripts/deploy.sh
#        DRY_RUN=true ./scripts/deploy.sh
#

set -eu

# Configuration
DEPLOY_ENV=${DEPLOY_ENV:-dev}
DRY_RUN=${DRY_RUN:-false}

# Select params file based on environment
if [[ "${DEPLOY_ENV}" = "dev" ]]; then
    PARAMS_FILE=dev-parameters.env
else
    PARAMS_FILE=parameters.env
fi

# --- Functions ---

get_snapshot_id() {
    # Fetch and validate SnapshotId from SSM parameter store.
    # Returns snapshot ID if valid, empty string otherwise.
    local ssm_param="${DEPLOY_ENV}_staking_snapshot"
    local snapshot_id

    if ! snapshot_id=$(aws ssm get-parameter --name "${ssm_param}" --query 'Parameter.Value' --output text 2>/dev/null); then
        echo "ℹ️  No snapshot parameter found, starting fresh" >&2
        return
    fi

    if [[ -z "${snapshot_id}" ]] || ! aws ec2 describe-snapshots --snapshot-ids "${snapshot_id}" &>/dev/null; then
        echo "⚠️  Snapshot ${snapshot_id} not found or invalid, starting fresh" >&2
        return
    fi

    echo "📦 Found valid snapshot: ${snapshot_id}" >&2
    echo "${snapshot_id}"
}

deploy_stack() {
    # Deploy CloudFormation stack.
    # Read params file into array (one param per line)
    local -a params=()
    while IFS= read -r line || [[ -n "${line}" ]]; do
        [[ -n "${line}" ]] && params+=("${line}")
    done < "${PARAMS_FILE}"
    params+=("SnapshotId=${SNAPSHOT_ID}")

    local -a args=(
        --stack-name "ECS-${DEPLOY_ENV}-staking-cluster"
        --template-file template.yaml
        --parameter-overrides "${params[@]}"
        --capabilities CAPABILITY_NAMED_IAM
        --no-fail-on-empty-changeset
    )

    if [[ "${DRY_RUN}" = "true" ]]; then
        echo "🔍 Dry run mode - creating changeset without executing"
        aws cloudformation deploy "${args[@]}" --no-execute-changeset
        echo "✅ Changeset created. Review in AWS Console before executing."
        return 1  # Signal dry run to skip ECS update
    fi

    aws cloudformation deploy "${args[@]}"
}

update_ecs_service() {
    # Force new deployment of ECS service.
    # https://docs.aws.amazon.com/cli/latest/reference/ecs/update-service.html
    aws ecs update-service \
        --cluster "${DEPLOY_ENV}-staking-cluster" \
        --service "${DEPLOY_ENV}_staking_service" \
        --task-definition "${DEPLOY_ENV}_eth_staker" \
        --force-new-deployment
}

# --- Main ---

SNAPSHOT_ID=$(get_snapshot_id)

if deploy_stack; then
    update_ecs_service
fi
