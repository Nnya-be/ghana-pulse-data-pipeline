SELECT p.page_id FROM pages AS p
LEFT JOIN page_likes as pl 
  ON p.page_id = pl.page_id
  WHERE pl.liked_date ISNULL
ORDER BY 1;
