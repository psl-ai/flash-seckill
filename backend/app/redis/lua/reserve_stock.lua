-- KEYS[1] stock, KEYS[2] user reservation, KEYS[3] idempotency record
-- ARGV[1] reservation id, ARGV[2] TTL seconds
local stock = tonumber(redis.call("GET", KEYS[1]) or "0")
if stock <= 0 then
  return {"SOLD_OUT"}
end
if redis.call("EXISTS", KEYS[2]) == 1 then
  return {"ALREADY_REGISTERED", redis.call("GET", KEYS[2])}
end
if redis.call("EXISTS", KEYS[3]) == 1 then
  return {"IDEMPOTENT_REPLAY", redis.call("GET", KEYS[3])}
end
redis.call("DECR", KEYS[1])
redis.call("SET", KEYS[2], ARGV[1], "EX", ARGV[2])
redis.call("SET", KEYS[3], ARGV[1], "EX", ARGV[2])
return {"SUCCESS", ARGV[1]}
