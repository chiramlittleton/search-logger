#!/bin/bash

API_URL="http://localhost:8082/log"

KEYWORDS=("ai" "crypto" "blockchain" "business" "cloud" "kubernetes" "golang" "python")

echo "🔁 Sending 10 test search logs to $API_URL"

for i in {1..10}; do
  keyword=${KEYWORDS[$RANDOM % ${#KEYWORDS[@]}]}
  session_id=$(uuidgen)
  user_id=$(uuidgen)

  payload=$(cat <<EOF
{
  "keyword": "$keyword",
  "user_id": "$user_id",
  "session_id": "$session_id"
}
EOF
)

  echo "→ POST $keyword"
  curl -s -X POST "$API_URL" \
       -H "Content-Type: application/json" \
       -d "$payload"

  echo -e "\n---"
  sleep 0.2
done

echo "✅ Done"