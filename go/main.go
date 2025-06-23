package main

import (
	"github.com/gin-gonic/gin"
	"github.com/jackc/pgx/v5"
	"github.com/redis/go-redis/v9"
)

type SearchPayload struct {
	Keyword   string `json:"keyword"`
	UserID    string `json:"user_id"`
	SessionID string `json:"session_id"`
}

func main() {
	// Connect to Redis
	rdb := redis.NewClient(&redis.Options{
		Addr: "redis:6379", // Adjust if needed
	})

	// Connect to Postgres
	db, err := pgx.Connect(ctx, "postgres://search:search@postgres:5432/search_logs")
	if err != nil {
		panic(err)
	}

	logger := &Logger{
		Redis: rdb,
		DB:    db,
	}

	// Start background flush loop
	go logger.FlushLoop()

	// HTTP API
	router := gin.Default()
	router.POST("/log", func(c *gin.Context) {
		var payload SearchPayload
		if err := c.BindJSON(&payload); err != nil {
			c.JSON(400, gin.H{"error": "invalid payload"})
			return
		}
		if err := logger.SaveSearch(payload.Keyword, payload.SessionID, payload.UserID); err != nil {
			c.JSON(500, gin.H{"error": "failed to store search"})
			return
		}
		c.JSON(200, gin.H{"status": "ok"})
	})

	router.Run(":8080")
}
