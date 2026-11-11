WITH grouped_tweets AS (
  SELECT user_id, count(msg) AS tweet_bucket
    FROM tweets AS t
    WHERE TO_CHAR(tweet_date, 'YYYY') = '2022'
    GROUP BY user_id
)
SELECT tweet_bucket, 
  count(user_id) AS users_num
  from grouped_tweets
GROUP BY 1
ORDER BY 2 DESC;