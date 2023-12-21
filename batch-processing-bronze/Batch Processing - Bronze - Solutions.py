# Databricks notebook source
# MAGIC %md
# MAGIC # Batch Processing - Bronze Layer
# MAGIC
# MAGIC When creating long-term storage for analytical use cases, the first step is to ingest data for the source, with a shape as close as possible to the original shape. As the first step in our data processing journey, this allows us to 
# MAGIC 1. create a "checkpoint" or "save zone" so that we can more easily debug issues and determine if there were issues at this step or downstream
# MAGIC 2. replay data to downstream steps in the case that there is an error or interruption (data is idempotent)
# MAGIC
# MAGIC In this exercise, we will:
# MAGIC * ingest the raw data in a single pull
# MAGIC * convert the data to parquet format (a format good for downstream reading)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Set up this Notebook
# MAGIC Before we get started, we need to quickly set up this notebook by installing a helpers, cleaning up your unique working directory (as to not clash with others working in the same space), and setting some variables. Run the following cells using shift + enter. **Note** that if your cluster shuts down, you will need to re-run the cells in this section.

# COMMAND ----------

# MAGIC %pip uninstall -y databricks_helpers exercise_ev_databricks_unit_tests
# MAGIC %pip install git+https://github.com/data-derp/databricks_helpers#egg=databricks_helpers git+https://github.com/data-derp/exercise_ev_databricks_unit_tests#egg=exercise_ev_databricks_unit_tests

# COMMAND ----------

exercise_name = "batch_processing_bronze_ingest"

# COMMAND ----------

from databricks_helpers.databricks_helpers import DataDerpDatabricksHelpers

helpers = DataDerpDatabricksHelpers(dbutils, exercise_name)

current_user = helpers.current_user()
working_directory = helpers.working_directory()

print(f"Your current working directory is: {working_directory}")

# COMMAND ----------

## This function CLEARS your current working directory. Only run this if you want a fresh start or if it is the first time you're doing this exercise.
helpers.clean_working_directory()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Read OCPP Data
# MAGIC We've done this a couple of times before! Run the following cells to download the data to local storage and create a DataFrame from it.

# COMMAND ----------

url = "https://raw.githubusercontent.com/kelseymok/charge-point-simulator-v1.6/main/out/1680355141.csv.gz"
filepath = helpers.download_to_local_dir(url)

# COMMAND ----------

from pyspark.sql import DataFrame
from pyspark.sql.types import StructType, StructField, StringType, IntegerType

def create_dataframe(filepath: str) -> DataFrame:
    
    custom_schema = StructType([
        StructField("message_id", StringType(), True),
        StructField("message_type", IntegerType(), True),
        StructField("charge_point_id", StringType(), True),
        StructField("action", StringType(), True),
        StructField("write_timestamp", StringType(), True),
        StructField("body", StringType(), True),
    ])
    
    df = spark.read.format("csv") \
        .option("header", True) \
        .option("delimiter", ",") \
        .option("escape", "\\") \
        .schema(custom_schema) \
        .load(filepath)
    return df
    
df = create_dataframe(filepath)
display(df)


# COMMAND ----------

# MAGIC %md
# MAGIC ## EXERCISE: Write to Parquet
# MAGIC Now that we have our ingested data represented in a DataFrame, let's use the [parquet writer](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrameWriter.parquet.html) along with [mode="overwrite"](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrameWriter.parquet.html) to formally write our data to the specified `out_dir`.

# COMMAND ----------

def write(input_df: DataFrame):
    out_dir = f"{working_directory}/output/"
    
    ### YOUR CODE HERE ###
    mode_name = None
    ###
    input_df. \
        write. \
        mode(mode_name). \
        parquet(out_dir)
    
write(df)

# COMMAND ----------

########## SOLUTION ############

def write(input_df: DataFrame):
    out_dir = f"{working_directory}/output/"
    
    ### YOUR CODE HERE ###
    mode_name = "overwrite"
    ###
    input_df. \
        write. \
        mode(mode_name). \
        parquet(out_dir)
    
    
write(df)

# COMMAND ----------

# MAGIC %md
# MAGIC Let's inspect what we've created.

# COMMAND ----------

dbutils.fs.ls(f"{working_directory}/output/")

# COMMAND ----------

# MAGIC %md
# MAGIC #### E2E Test

# COMMAND ----------

from exercise_ev_databricks_unit_tests.batch_processing_bronze import test_write_e2e

test_write_e2e(dbutils.fs.ls(f"{working_directory}/output"), spark, display)


# COMMAND ----------

# MAGIC %md
# MAGIC ## Reflect
# MAGIC * How many in-memory partitions were created as a result of the write in CMD 11 above ?  
# MAGIC **Answer:** Well, the writes usually engage one of the worker machine's core to process output to the disk, and therefore only one task. You can check this out in various ways as follows:  
# MAGIC   a) Go to `View`-> `View Spark UI` in this notebook and checkout the details with respect to Job number in `CMD 12` above.   
# MAGIC   b) Checkout the number of `part-0000` files in `CMD 14` above.  
# MAGIC   c) In this notebook on the left hand side, go to `Catalog`-> `Browse DBFS`-> `/FileStore/<your_user_name>/batch_processing_bronze_ingest/output` and checkout the number of files there. It should be 1 only.  
# MAGIC * How much time does it takes to write and why ?  
# MAGIC **Answer:** It should ideally take from about 20 seconds to half a minute to write the data. It takes that much time because the worker machine is writing data to the disk on S3
# MAGIC * How many minutes were spent showing the response in the notebook as opposed to the actual write ?
# MAGIC **Answer:** Ideally half a minute to write the data and a few seconds more to show it back in the notebook
# MAGIC
