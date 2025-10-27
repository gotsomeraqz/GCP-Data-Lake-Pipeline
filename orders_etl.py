
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_timestamp, when, lit, unix_timestamp, avg, sum as _sum, count as _count

spark = SparkSession.builder.appName("orders-etl").getOrCreate()

project_id = "zdatalake-476323"
bronze = "gs://raqz-bronze"
silver = "gs://raqz-silver"
gold = "gs://raqz-gold"

orders = spark.read.option("header", "true").csv(bronze+ "/orders/*/*.csv")
restaurants = spark.read.option("header", "true").csv(bronze+"/restaurants/*.csv")

orders = (orders
  .withColumn("order_ts", to_timestamp(col("order_ts")))
  .withColumn("delivered_ts", to_timestamp(col("delivered_ts")))
  .withColumn("order_value", col("order_value").cast("double"))
  .withColumn("promised_mins", col("promised_mins").cast("int"))
  .withColumn("late_delivery",
              when((col("status")=="DELIVERED") &
                   (unix_timestamp("delivered_ts") - unix_timestamp("order_ts") > col("promised_mins")*60),
                   lit(1)).otherwise(lit(0)))
  .withColumn("dt", col("order_ts").cast("date"))
)

(orders.write.mode("overwrite").partitionBy("dt").parquet(silver+"/orders"))
(restaurants.write.mode("overwrite").parquet(silver+"/restaurants"))

orders_silver = spark.read.parquet(silver+"/orders")
restaurants_silver = spark.read.parquet(silver+"/restaurants")

orders_enriched = (orders_silver.alias("o")
  .join(restaurants_silver.alias("r"), col("o.restaurant_id")==col("r.restaurant_id"), "left")
)

daily_rest_metrics = (orders_enriched
  .where(col("status")=="DELIVERED")
  .groupBy("dt", "o.restaurant_id", "r.name", "r.cuisine", "o.city")
  .agg(
    _count(lit(1)).alias("orders_delivered"),
    _sum("order_value").alias("gmv"),
    avg((unix_timestamp("delivered_ts") - unix_timestamp("order_ts"))/60.0).alias("avg_delivery_mins"),
    _sum("late_delivery").alias("late_count")
  )
  .withColumn("late_rate", col("late_count")/col("orders_delivered"))
)

(daily_rest_metrics.write.mode("overwrite").partitionBy("dt").parquet(gold+"/daily_restaurant_metrics"))
