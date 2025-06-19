```sql
sqlite> .schema v3pic
CREATE TABLE v3pic (
	id INTEGER NOT NULL, 
	name VARCHAR, 
	level VARCHAR, 
	style VARCHAR, 
	lang VARCHAR, 
	pic_type VARCHAR, 
	wordlib VARCHAR, 
	collection VARCHAR, 
	answer_text VARCHAR, 
	answer_location JSON, 
	prefix_path VARCHAR, 
	location VARCHAR, 
	PRIMARY KEY (id)
);
CREATE INDEX pictype_lang_level_index ON v3pic (pic_type, lang, level);
sqlite> select pic_type, lang, level, min(id), max(id), count(id) from v3pic group by 1,2,3;
icon|zh|l1|90001|100000|10000
nine|en|l1|110001|120000|10000
nine|zh|l1|60001|90000|30000
nine|zht|l1|100001|110000|10000
pencil|zh|l1|140001|142000|2000
phrase|zh|l1|30001|60000|30000
space|en|l1|130001|140000|10000
space|zh|l1|120001|130000|10000
word|zh|l1|1|30000|30000

```



- sqlite原生提供随机返回集合中的一个

以后写sqlite扩展插件, 最好的 sqlite 随机查询是写一个sqlite扩展支持查询集随机返回一个. 类似于 random.choice(list) 的逻辑.


- 其次是用最大值减去最小值, 然后用随机数对这个取余数. 然后再加上最小值当作随机的基准值供外侧的条件查询, 这样不需要去排序.

```sql
当过滤后查询集只有一行时, Max(id) - Min(id) 为0, 这个时候 num % 0 是 null, 所以需要coalesce来返回第一个非null的数字用于兜底.
SELECT * 
FROM   v3pic 
WHERE  pic_type = 'word' 
       AND lang = 'zh' 
       AND level = 'l1' 
       AND id >= (SELECT Coalesce(Abs(Random())% ( Max(id) - Min(id) ), 0) + Coalesce(Min(id), 0) 
                  FROM   v3pic 
                  WHERE  pic_type = 'word' 
                         AND lang = 'zh' 
                         AND level = 'l1') 
LIMIT  1; 
```

- 变体是用 count(id) 找到区间段, 这样可能会有数据偏置的风险.

```sql
SELECT * 
FROM   v3pic 
WHERE  pic_type = 'word' 
       AND lang = 'zh' 
       AND level = 'l1' 
       AND id >= (SELECT Coalesce(Abs(Random())% Count(id), 0) + Coalesce(Min(id), 0)
                  FROM   v3pic 
                  WHERE  pic_type = 'word' 
                         AND lang = 'zh' 
                         AND level = 'l1') 
LIMIT  1; 
```

- 在语义和查询性能之间兼容的就是对索引查询出来的 id 进行随机排序返回第一个当作外面的查询的过滤条件.


```sql
SELECT * 
FROM   v3pic 
WHERE  id IN (SELECT id 
              FROM   v3pic 
              WHERE  pic_type = 'word' 
                     AND lang = 'zh' 
                     AND level = 'l1' 
              ORDER  BY Random() 
              LIMIT  1); 
```

- 语义最简单, 性能最差

```sql

SELECT * 
FROM   v3pic 
WHERE  pic_type = 'word' 
       AND lang = 'zh' 
       AND level = 'l1' 
ORDER  BY Random() 
LIMIT  1; 
```