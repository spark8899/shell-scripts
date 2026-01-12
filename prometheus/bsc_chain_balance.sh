#!/usr/bin/env bash
# cron:
# */10 * * * * if /etc/node_exporter/scripts/bsc_balance.sh > /etc/node_exporter/bsc_balance.prom.$$; then mv /etc/node_exporter/bsc_balance.prom.$$ /etc/node_exporter/bsc_balance.prom; else rm /etc/node_exporter/bsc_balance.prom.$$;fi
set -euo pipefail
IFS=$'\n\t'

###############################################################################
# 1. Configuration
###############################################################################

RPC_URL="https://bsc-dataseed.binance.org/"
BALANCE_OF_SIG="0x70a08231"

ADDRESS_LIST=(
  "0xd8cc6BFDEe087148c220E9141a075D18418aBBaC bnb"
  "0x3A1008024ff1653d78170C18aFBEf8bF92eEfA2f usdt"
)


get_token_addr() {
  case "$1" in
    bnb)  echo "native" ;;
    usdt) echo "0x55d398326f99059ff775485246999027b3197955" ;;
    usdc) echo "0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d" ;;
    *)    return 1 ;;
  esac
}

get_token_decimals() {
  case "$1" in
    bnb|usdt|usdc) echo "18" ;;
    *)             echo "18" ;;
  esac
}

###############################################################################
# 2. Helper Functions (infra / low-level)
###############################################################################

json_rpc() {
  local payload="$1"
  curl -s --max-time 10 -X POST \
    -H "Content-Type: application/json" \
    --data "$payload" \
    "$RPC_URL"
}

hex_to_decimal() {
  local hex="$1"
  local decimals="$2"

  python3 - <<PY
h = "$hex"
d = int("$decimals")
try:
    v = int(h, 16)
    out = "{:.18f}".format(v / (10 ** d)).rstrip('0').rstrip('.')
    print(out if out else "0")
except Exception:
    print("0")
PY
}

addr_to_hex() {
  local addr="$1"
  printf '%064s' "${addr#0x}" | tr '[:upper:]' '[:lower:]' | tr ' ' '0'
}

###############################################################################
# 3. Blockchain Query Functions
###############################################################################

get_native_balance_hex() {
  local addr="$1"
  json_rpc "{\"jsonrpc\":\"2.0\",\"method\":\"eth_getBalance\",\"params\":[\"$addr\",\"latest\"],\"id\":1}" \
    | jq -r '.result // empty'
}

get_erc20_balance_hex() {
  local addr_hex="$1"
  local contract="$2"
  json_rpc "{\"jsonrpc\":\"2.0\",\"method\":\"eth_call\",\"params\":[{\"to\":\"$contract\",\"data\":\"${BALANCE_OF_SIG}${addr_hex}\"},\"latest\"],\"id\":1}" \
    | jq -r '.result // empty'
}

###############################################################################
# 4. Business Logic
###############################################################################

emit_metric() {
  local addr="$1"
  local token="$2"
  local value="$3"
  printf 'bsc_balance{addr="%s",token="%s"} %s\n' "$addr" "$token" "$value"
}

process_address() {
  local addr="$1"
  local token="$2"
  local addr_hex
  addr_hex="$(addr_to_hex "$addr")"

  local hex=""
  local balance="0"

  local token_addr
  if ! token_addr="$(get_token_addr "$token")"; then
    echo "Error: Unknown token '$token' for address '$addr'" >&2
    return
  fi

  local token_decimals
  token_decimals="$(get_token_decimals "$token")"

  if [[ "$token_addr" == "native" ]]; then
    hex="$(get_native_balance_hex "$addr")"
  else
    hex="$(get_erc20_balance_hex "$addr_hex" "$token_addr")"
  fi

  if [[ -n "$hex" ]]; then
    balance="$(hex_to_decimal "$hex" "$token_decimals")"
  fi

  emit_metric "$addr" "$token" "$balance"
}

###############################################################################
# 5. Main
###############################################################################

main() {
  for entry in "${ADDRESS_LIST[@]}"; do
    local addr
    local token
    IFS=' ' read -r addr token <<< "$entry"
    if [[ -n "$addr" && -n "$token" ]]; then
      process_address "$addr" "$token"
    else
      echo "Warning: Invalid entry '$entry'. Format should be 'ADDRESS TOKEN'" >&2
    fi
  done
}

main "$@"
