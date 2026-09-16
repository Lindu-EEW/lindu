curl -s -X POST -H "Content-Type: application/json" -u admin:admin -d '{
  "queries": [
    {
      "refId": "A",
      "datasourceId": 1,
      "rawSql": "SELECT time, pga FROM sensor_telemetry ORDER BY time DESC LIMIT 5",
      "format": "table"
    }
  ]
}' http://localhost:3000/api/tsdb/query
