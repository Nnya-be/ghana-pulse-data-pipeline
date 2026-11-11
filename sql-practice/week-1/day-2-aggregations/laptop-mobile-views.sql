SELECT count(device_type) FILTER(WHERE device_type = 'laptop') AS laptop_views,
  count(device_type) FILTER(WHERE device_type IN ('phone', 'tablet') )AS mobile_views
FROM viewership;