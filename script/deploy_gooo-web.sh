#!/bin/bash
set -euo pipefail

SCRIPT_NAME=$(basename "$0")
LOCK_FILE="/tmp/${SCRIPT_NAME%.sh}.lock"

FILE_PATH="/opt/code/gooo-web"
DEPLOY_NAME="website-gooo-web"
DEPLOY_ORIGIN="branch1966"
BUILD_OUTPUT_DIR="dist"

LOG_FILE="/opt/code/deploy_${DEPLOY_NAME}_$(date +%F).log"

main_logic() {
  find "/opt/code" -maxdepth 1 -name "deploy_${DEPLOY_NAME}_*.log" ! -name "$(basename "$LOG_FILE")" -type f -delete

  cd "$FILE_PATH" || {
    echo "ERROR: directory not exists $FILE_PATH"
    exit 1
  }

  echo "================================="
  echo "deploy ${SCRIPT_NAME%.sh}"
  echo "StartTime: $(date '+%Y-%m-%d %H:%M:%S')"
  echo "Target branch: ${DEPLOY_ORIGIN}"
  echo "================================="

  echo "##### fetch code"
  git fetch origin
  NEED_BUILD=false

  CURRENT_BRANCH=$(git branch --show-current)
  echo "Current branch: ${CURRENT_BRANCH}"

  if [ "$CURRENT_BRANCH" != "$DEPLOY_ORIGIN" ]; then
    echo "Switch branch ${CURRENT_BRANCH} -> ${DEPLOY_ORIGIN}"
    NEED_BUILD=true
    if git show-ref --verify --quiet "refs/heads/${DEPLOY_ORIGIN}"; then
      git checkout "${DEPLOY_ORIGIN}"
    else
      echo "Local branch ${DEPLOY_ORIGIN} not found"
      echo "Create branch from origin/${DEPLOY_ORIGIN}"
      git checkout -b "${DEPLOY_ORIGIN}" "origin/${DEPLOY_ORIGIN}"
    fi
  fi

  echo "##### check update"
  LOCAL=$(git rev-parse HEAD)
  REMOTE=$(git rev-parse "origin/${DEPLOY_ORIGIN}")

  echo "LOCAL: $LOCAL"
  echo "REMOTE: $REMOTE"

  if [ "$LOCAL" != "$REMOTE" ]; then
    NEED_BUILD=true
  fi
  echo "NEED_BUILD: ${NEED_BUILD}"

  if [ "$NEED_BUILD" = true ]; then
    echo "##### update code"
    git reset --hard "origin/${DEPLOY_ORIGIN}"
    git clean -fd

    echo "##### build code."
    { pnpm install && pnpm run build:prod; } | tee -a "$LOG_FILE"

    if [ ! -d "$BUILD_OUTPUT_DIR" ]; then
      echo "ERROR: build failed, $BUILD_OUTPUT_DIR not found"
      if [ -f "$LOG_FILE" ]; then
        echo -e "Subject: build error.\n\n$(cat "$LOG_FILE")" | sendmail -v sss@abcd.com
      fi
      exit 1
    fi

    echo "##### backup files"
    rm -rf "/opt/apps/${DEPLOY_NAME}_old"

    if [ -d "/opt/apps/${DEPLOY_NAME}" ]; then
      mv "/opt/apps/${DEPLOY_NAME}" "/opt/apps/${DEPLOY_NAME}_old"
    fi

    echo "##### deploy code"
    mv "$BUILD_OUTPUT_DIR" "/opt/apps/${DEPLOY_NAME}"
    echo "##### deploy success"
  else
    echo "Up-to-date (Branch matches and no new commits)"
  fi

  echo "EndTime: $(date +'%Y-%m-%d %H:%M:%S')"
  echo ""
  return 0
}

(
  flock -n -x 9 || {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - [WARN] ${SCRIPT_NAME%.sh} Another instance is running. Exit."
    exit 1
  }

  echo "$(date '+%Y-%m-%d %H:%M:%S') - [INFO] ${SCRIPT_NAME%.sh} The lock has been successfully acquired, and the main logic is ready to be executed."

  main_logic

) 9> "$LOCK_FILE"
