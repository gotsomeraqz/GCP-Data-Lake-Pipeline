# 🔥 GCP Data Lake Pipeline

End-to-End Zomato-Style Orders Analytics using Google Cloud Platform

## 📋 Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Setup Instructions](#setup-instructions)
- [Pipeline Stages](#pipeline-stages)
- [Usage](#usage)
- [SQL Analytics](#sql-analytics)
- [Business Value](#business-value)
- [Tech Stack](#tech-stack)

## 🎯 Overview

This project implements a complete data lakehouse architecture on Google Cloud Platform, transforming raw order data through Bronze → Silver → Gold layers, culminating in business-ready analytics in BigQuery and Looker Studio dashboards.

### Key Features
- ✅ Multi-layer data lake (Bronze/Silver/Gold)
- ✅ Automated ETL with Apache Spark on Dataproc
- ✅ Type-safe Parquet storage
- ✅ BigQuery external tables for SQL analytics
- ✅ Real-time KPI calculations
- ✅ Dashboard-ready metrics

## 🏗️ Architecture

```
Raw CSV Data (Bronze)
        ↓
    Spark ETL
        ↓
Clean Parquet (Silver)
        ↓
    Spark Aggregations
        ↓
Business KPIs (Gold)
        ↓
    BigQuery External Tables
        ↓
    Looker Studio Dashboard
```

## 📦 Prerequisites

### GCP Services Required
- Google Cloud Storage
- Dataproc (Managed Spark)
- BigQuery
- Looker Studio (optional, for visualization)

### Local Development
- Python 3.8+
- PySpark 3.x
- Google Cloud SDK
- Service Account with appropriate permissions

### Required GCP Permissions
```
- Storage Admin (for GCS buckets)
- Dataproc Admin (for Spark clusters)
- BigQuery Admin (for external tables)
```

## 🚀 Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/gcp-data-lake-pipeline.git
cd gcp-data-lake-pipeline
```

### 2. Set Up GCP Project
```bash
# Set your GCP project
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable dataproc.googleapis.com
gcloud services enable bigquery.googleapis.com
gcloud services enable storage-api.googleapis.com
```

### 3. Create GCS Buckets
```bash
# Create buckets for each layer
gsutil mb -l us-central1 gs://sb-bronze
gsutil mb -l us-central1 gs://sb-silver
gsutil mb -l us-central1 gs://sb-gold
```

### 4. Upload Sample Data
```bash
# Upload your raw CSV files to Bronze layer
gsutil cp data/orders.csv gs://sb-bronze/orders/
```

### 5. Create Dataproc Cluster
```bash
gcloud dataproc clusters create data-pipeline-cluster \
    --region=us-central1 \
    --zone=us-central1-a \
    --master-machine-type=n1-standard-4 \
    --worker-machine-type=n1-standard-4 \
    --num-workers=2 \
    --image-version=2.1-debian11
```

### 6. Install Dependencies
```bash
pip install -r requirements.txt
```

## 📊 Pipeline Stages

### 🥉 Bronze Layer
**Purpose:** Raw data ingestion

- **Location:** `gs://sb-bronze/orders/`
- **Format:** CSV
- **Content:** Raw order data as received from source systems
- **Schema:** No transformation, original structure maintained

### 🥈 Silver Layer
**Purpose:** Cleaned and typed data

- **Location:** `gs://sb-silver/orders/`
- **Format:** Parquet (columnar, compressed)
- **Transformations:**
  - String → Timestamp conversion
  - Numeric type casting
  - Add `late_delivery` flag (0/1)
  - Add partition column `dt`
  - Schema validation & consistency checks

**Run Silver Transformation:**
```bash
spark-submit \
    --master yarn \
    --deploy-mode cluster \
    scripts/bronze_to_silver.py
```

### 🥇 Gold Layer
**Purpose:** Business KPIs and aggregated metrics

- **Location:** `gs://sb-gold/daily_metrics/`
- **Format:** Parquet
- **Metrics Calculated:**
  - `orders_delivered` per restaurant
  - `gmv` (Gross Merchandise Value)
  - `avg_delivery_mins`
  - `late_count` & `late_rate`
  - Daily aggregations by restaurant and city

**Run Gold Aggregation:**
```bash
spark-submit \
    --master yarn \
    --deploy-mode cluster \
    scripts/silver_to_gold.py
```

## 💾 BigQuery Integration

### Create External Table
```sql
CREATE EXTERNAL TABLE `my-data-lake-project.food_analytics.daily_restaurant_metrics_ext`
(
  dt DATE,
  name STRING,
  city STRING,
  orders_delivered INT64,
  gmv FLOAT64,
  avg_delivery_mins FLOAT64,
  late_count INT64,
  late_rate FLOAT64
)
OPTIONS (
  format = 'PARQUET',
  uris = ['gs://sb-gold/daily_metrics/*.parquet']
);
```

## 🔍 SQL Analytics

### Example Queries

**Find restaurants with high late delivery rates:**
```sql
SELECT dt, name, city, gmv, late_rate
FROM `my-data-lake-project.food_analytics.daily_restaurant_metrics_ext`
WHERE late_rate > 0.3
ORDER BY gmv DESC;
```

**Top performing restaurants by GMV:**
```sql
SELECT 
  name,
  city,
  SUM(gmv) as total_gmv,
  AVG(late_rate) as avg_late_rate,
  AVG(avg_delivery_mins) as avg_delivery_time
FROM `my-data-lake-project.food_analytics.daily_restaurant_metrics_ext`
WHERE dt >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY name, city
ORDER BY total_gmv DESC
LIMIT 10;
```

**City-wise delivery performance:**
```sql
SELECT 
  city,
  COUNT(DISTINCT name) as num_restaurants,
  SUM(orders_delivered) as total_orders,
  AVG(avg_delivery_mins) as avg_delivery_time,
  AVG(late_rate) as avg_late_rate
FROM `my-data-lake-project.food_analytics.daily_restaurant_metrics_ext`
GROUP BY city
ORDER BY total_orders DESC;
```

## 💡 Business Value

### 🏆 Performance Insights
Identify best and worst performing restaurants by GMV and delivery metrics to make informed business decisions.

### ⏱️ Delivery Optimization
Optimize delivery times per city and reduce late delivery rates through data-driven process improvements.

### 😊 Customer Satisfaction
Improve customer experience by addressing bottlenecks and operational inefficiencies revealed through analytics.

## 🛠️ Tech Stack

| Technology | Purpose |
|------------|---------|
| **Google Cloud Storage** | Scalable object storage for Bronze, Silver & Gold data layers with partitioned directory structure |
| **Dataproc (Apache Spark)** | Managed Spark clusters for distributed data processing and ETL transformations |
| **BigQuery** | Serverless data warehouse with external tables for fast SQL analytics and dashboard integration |
| **Looker Studio** | Interactive dashboards for business intelligence and reporting |

## 📁 Project Structure

```
gcp-data-lake-pipeline/
├── data/
│   └── orders.csv              # Sample raw data
├── scripts/
│   ├── bronze_to_silver.py     # Silver layer transformation
│   ├── silver_to_gold.py       # Gold layer aggregation
│   └── create_external_table.sql
├── notebooks/
│   └── data_exploration.ipynb  # Jupyter notebook for analysis
├── config/
│   └── pipeline_config.yaml    # Configuration settings
├── docs/
│   └── pipeline_ui.html        # Visual pipeline documentation
├── requirements.txt
├── README.md
└── LICENSE
```

## 🔄 Running the Complete Pipeline

```bash
# 1. Upload data to Bronze
gsutil cp data/orders.csv gs://sb-bronze/orders/

# 2. Transform to Silver
spark-submit scripts/bronze_to_silver.py

# 3. Aggregate to Gold
spark-submit scripts/silver_to_gold.py

# 4. Create BigQuery external table
bq query --use_legacy_sql=false < scripts/create_external_table.sql

# 5. Query and analyze
bq query "SELECT * FROM food_analytics.daily_restaurant_metrics_ext LIMIT 10"
```

## 📈 Monitoring and Maintenance

### Check Pipeline Status
```bash
# View recent Spark jobs
gcloud dataproc jobs list --region=us-central1

# Check bucket contents
gsutil ls -r gs://sb-gold/daily_metrics/
```

### Cost Optimization
- Use preemptible workers in Dataproc clusters
- Set lifecycle policies on GCS buckets
- Enable BigQuery slot reservations for predictable costs
- Schedule pipeline runs during off-peak hours

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Built with ❤️ for the data engineering community

---

**⭐ If you find this project helpful, please consider giving it a star!**
