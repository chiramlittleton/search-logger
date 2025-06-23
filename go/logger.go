package main

import (
	"context"
	"encoding/json"
	"fmt"
	"strconv"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/redis/go-redis/v9"
)

var ctx = context.Background()
var debounceWindow = 3 * time.Second
var flushInterval = 1 * time.Second

type Logger struct {
	Redis *redis.Client
	DB    *pgx.Conn
}

type DebounceEntry struct {
	Keyword   string `json:"keyword"`
	UserID    string `json:"user_id"`
	UpdatedAt int64  `json:"updated_at"`
}

func (l *Logger) SaveSearch(keyword, sessionID, userID string) error {
	entry := DebounceEntry{
		Keyword:   keyword,
		UserID:    userID,
		UpdatedAt: time.Now().Unix(),
	}

	data, err := json.Marshal(entry)
	if err != nil {
		return err
	}

	// Store in hash
	if err := l.Redis.Set(ctx, "debounce:"+sessionID, data, 0).Err(); err != nil {
		return err
	}

	// Track in sorted set by timestamp
	if err := l.Redis.ZAdd(ctx, "debounce:updated", redis.Z{
		Score:  float64(entry.UpdatedAt),
		Member: sessionID,
	}).Err(); err != nil {
		return err
	}

	return nil
}

func (l *Logger) FlushLoop() {
	ticker := time.NewTicker(flushInterval)
	defer ticker.Stop()

	for range ticker.C {
		cutoff := time.Now().Add(-debounceWindow).Unix()

		// Get session IDs that haven't been updated recently
		sessionIDs, err := l.Redis.ZRangeByScore(ctx, "debounce:updated", &redis.ZRangeBy{
			Min: "0",
			Max: strconv.FormatInt(cutoff, 10),
		}).Result()

		if err != nil {
			fmt.Println("[ERROR] Redis ZRangeByScore:", err)
			continue
		}

		for _, sessionID := range sessionIDs {
			key := "debounce:" + sessionID

			val, err := l.Redis.Get(ctx, key).Result()
			if err != nil {
				fmt.Println("[WARN] missing debounce entry for", sessionID)
				// Still remove from tracking set
				l.Redis.ZRem(ctx, "debounce:updated", sessionID)
				continue
			}

			var entry DebounceEntry
			if err := json.Unmarshal([]byte(val), &entry); err != nil {
				fmt.Println("[ERROR] invalid debounce entry for", sessionID)
				l.Redis.ZRem(ctx, "debounce:updated", sessionID)
				continue
			}

			// Flush to Postgres
			_, dbErr := l.DB.Exec(ctx,
				`INSERT INTO search_logs (session_id, keyword, user_id) VALUES ($1, $2, $3)`,
				sessionID, entry.Keyword, entry.UserID)

			if dbErr != nil {
				fmt.Println("[ERROR] DB insert failed:", dbErr)
				continue
			}

			fmt.Printf("[FLUSH] session=%s keyword=%s\n", sessionID, entry.Keyword)

			// Clean up
			l.Redis.Del(ctx, key)
			l.Redis.ZRem(ctx, "debounce:updated", sessionID)
		}
	}
}
