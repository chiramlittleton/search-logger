#!/bin/bash

PORT=${1:-8082}
API_URL="http://localhost:$PORT/log"

DB_USER="search"
DB_NAME="search_logs"
DB_HOST="localhost"
DB_TABLE="search_logs"

# Array of simulated test cases: (keyword, uses_user_id)
declare -a TEST_CASES=(
  "business true"
  "search false"
  "marketing true"
  "python false"
)

flush_delay_secs=5

for TEST in "${TEST_CASES[@]}"; do
  BASE_KEYWORD=$(echo "$TEST" | awk '{print $1}')
  WITH_USER=$(echo "$TEST" | awk '{print $2}')
  SESSION_ID=$(uuidgen)
  USER_ID=$( [ "$WITH_USER" = "true" ] && uuidgen || echo "" )

  echo
  echo "🔁 Simulating keyword: '$BASE_KEYWORD'"
  echo "🧪 session_id=$SESSION_ID"
  if [ -n "$USER_ID" ]; then
    echo "👤 user_id=$USER_ID"
  else
    echo "👤 anonymous session"
  fi

  for (( i=1; i<=${#BASE_KEYWORD}; i++ )); do
    partial=${BASE_KEYWORD:0:$i}

    payload=$(cat <<EOF
{
  "keyword": "$partial",
  "session_id": "$SESSION_ID",
  "user_id": "$USER_ID"
}
EOF
)

    echo "→ Sending: $partial"
    curl -s -X POST "$API_URL" \
         -H "Content-Type: application/json" \
         -d "$payload" > /dev/null

    sleep 0.2
  done
done

echo
echo "⏳ Waiting $flush_delay_secs seconds for Redis flush..."
sleep $flush_delay_secs

echo
echo "🔍 Verifying results in Postgres:"
for TEST in "${TEST_CASES[@]}"; do
  BASE_KEYWORD=$(echo "$TEST" | awk '{print $1}')
  SESSION_ID=$(PGPASSWORD=search psql -U $DB_USER -d $DB_NAME -h $DB_HOST -Atc \
    "SELECT session_id FROM $DB_TABLE WHERE keyword = '$BASE_KEYWORD' ORDER BY created_at DESC LIMIT 1;")

  if [ -n "$SESSION_ID" ]; then
    echo "✅ '$BASE_KEYWORD' logged under session_id=$SESSION_ID"
  else
    echo "❌ '$BASE_KEYWORD' was not stored"
  fi
done
