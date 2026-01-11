#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Check required commands
for cmd in kubectl jq yq; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Error: required command '$cmd' is not installed or not in PATH."
    if [ "$cmd" = "jq" ]; then
      echo "Hint: install jq with 'apt install jq' or your package manager."
    elif [ "$cmd" = "yq" ]; then
      echo "Hint: install yq with 'apt install yq' (Ubuntu) or refer to official docs."
    elif [ "$cmd" = "kubectl" ]; then
      echo "Hint: install kubectl from Kubernetes official documentation."
    fi
    exit 1
  fi
done

# Check arguments
if [ $# -ne 2 ]; then
  echo "Usage: $0 <namespace> <deploy|sts>"
  exit 1
fi

NAMESPACE=$1
TYPE=$2

# Normalize resource type (support shorthand)
case "$TYPE" in
  Deployment|deployment|deploy|dep)
    RESOURCE="deployment"
    KIND="Deployment"
    TYPE="deploy"
    ;;
  StatefulSets|StatefulSet|statefulsets|statefulset|sts)
    RESOURCE="statefulset"
    KIND="StatefulSet"
    TYPE="statefulset"
    ;;
  *)
    echo "Invalid type: $TYPE"
    echo "Supported types:"
    echo "  Deployment | deploy | dep"
    echo "  StatefulSets | sts"
    exit 1
    ;;
esac

# Output directory
OUTPUT_DIR="./backup_${NAMESPACE}_${TYPE}"
mkdir -p "$OUTPUT_DIR"

echo "Backing up ${KIND} and related Services from namespace ${NAMESPACE}"

# Get all resource names
NAMES=$(kubectl get ${RESOURCE} -n ${NAMESPACE} -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}')

for NAME in $NAMES; do
  echo "Processing ${KIND}: ${NAME}"

  OUTPUT_FILE="${OUTPUT_DIR}/${NAME}.yaml"
  : > "$OUTPUT_FILE"

  # Export Deployment / StatefulSet
  kubectl get ${RESOURCE} ${NAME} -n ${NAMESPACE} -o json | \
  jq '
    {
      apiVersion,
      kind,
      metadata: {
        name: .metadata.name,
        namespace: .metadata.namespace,
        labels: .metadata.labels
      },
      spec: {
        replicas: .spec.replicas,
        selector: .spec.selector,
        template: {
          metadata: {
            annotations: (.spec.template.metadata.annotations // {} | del(.["cattle.io/timestamp"])),
            labels: .spec.template.metadata.labels
          },
          spec: (
            .spec.template.spec
            | walk(
                if type == "object"
                then with_entries(select(.value != {}))
                else .
                end
              )
          )
        }
      }
    }
  ' | yq -y >> "$OUTPUT_FILE"

  echo "---" >> "$OUTPUT_FILE"

  # Build selector from matchLabels using jq
  SELECTOR=$(kubectl get ${RESOURCE} ${NAME} -n ${NAMESPACE} -o json | \
    jq -r '
      .spec.selector.matchLabels
      | select(. != null)
      | to_entries
      | map("\(.key)=\(.value)")
      | join(",")
    ')

  # Find and export related Services
  if [ -n "$SELECTOR" ]; then
    SERVICES=$(kubectl get svc -n ${NAMESPACE} -l "$SELECTOR" \
      -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}' || true)

    for SVC in $SERVICES; do
      echo "  Exporting Service: ${SVC}"

      kubectl get svc ${SVC} -n ${NAMESPACE} -o json | \
      jq '
        {
          apiVersion,
          kind,
          metadata: {
            name: .metadata.name,
            namespace: .metadata.namespace,
            labels: .metadata.labels
          },
          spec: {
            ports: .spec.ports,
            selector: .spec.selector,
            type: .spec.type
          }
        }
      ' | yq -y >> "$OUTPUT_FILE"

      echo "---" >> "$OUTPUT_FILE"
    done
  fi

  # Remove trailing '---' at end of file
  sed -i '${/^---$/d;}' "$OUTPUT_FILE"
done

echo "Backup completed. Files are stored in ${OUTPUT_DIR}"

