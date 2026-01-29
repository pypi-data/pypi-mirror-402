# coeaidpml/core.py

from pyspark.sql import functions as F
from pyspark.sql.functions import expr, collect_list, concat_ws
from pyspark.sql import SparkSession
from pyspark.sql.types import ArrayType, StructType, StructField, StringType


def run_schema_analysis(
    spark: SparkSession,
    schema_name: str,
    model_id: str = "default.oci_ai_models.xai.grok-4",
    output_table: str = "bronze.default.ai_ml_usecases_structured"
):
    """
    Automatically analyzes schema, builds graph relationships,
    queries OCI LLM via expr('query_model'), and writes structured ML use cases.

    ⚙️ Behavior:
    - If running on an OCI AIDP Spark cluster: executes real query_model().
    - If running locally or no query_model() registered: returns mocked LLM output.
    """

    # -------------------------------------------------------------------------
    # 1️⃣ Validate schema and get table list
    # -------------------------------------------------------------------------
    tables_df = spark.sql(f"SHOW TABLES IN {schema_name}")
    tables = [row.tableName for row in tables_df.collect()]
    if not tables:
        raise ValueError(f"No tables found in schema {schema_name}")

    # -------------------------------------------------------------------------
    # 2️⃣ Collect schema metadata
    # -------------------------------------------------------------------------
    meta_list = []
    for tbl in tables:
        desc_df = spark.sql(f"DESCRIBE TABLE {schema_name}.{tbl}")
        desc_clean = desc_df.select(
            F.lit(tbl).alias("table_name"),
            F.col("col_name").alias("column_name"),
            F.col("data_type")
        )
        meta_list.append(desc_clean)

    schema_meta_df = meta_list[0]
    for df in meta_list[1:]:
        schema_meta_df = schema_meta_df.union(df)

    # -------------------------------------------------------------------------
    # 3️⃣ Build relationships (edges)
    # -------------------------------------------------------------------------
    edges = []
    for t1 in tables:
        cols1 = set(
            schema_meta_df.filter(F.col("table_name") == t1)
            .select("column_name").rdd.flatMap(lambda x: x).collect()
        )
        for t2 in tables:
            if t1 != t2:
                cols2 = set(
                    schema_meta_df.filter(F.col("table_name") == t2)
                    .select("column_name").rdd.flatMap(lambda x: x).collect()
                )
                common = cols1.intersection(cols2)
                if common:
                    edges.append((t1, t2, ", ".join(common)))

    if edges:
        edges_df = spark.createDataFrame(edges, ["src", "dst", "common_columns"])
        edges_summary = (
            edges_df.groupBy("src")
            .agg(concat_ws("; ", collect_list(F.concat(F.col("dst"), F.lit(" via "), F.col("common_columns")))).alias("relations"))
        )
    else:
        edges_summary = spark.createDataFrame([], "src STRING, relations STRING")

    # -------------------------------------------------------------------------
    # 4️⃣ Combine metadata and relationships into one string
    # -------------------------------------------------------------------------
    rel_df = (
        schema_meta_df.groupBy("table_name")
        .agg(concat_ws(", ", collect_list("column_name")).alias("columns"))
    )

    full_metadata_df = (
        rel_df.join(edges_summary, rel_df.table_name == edges_summary.src, "left")
        .drop("src")
        .fillna({"relations": "No detected relationships"})
        .withColumn(
            "metadata_summary",
            F.concat_ws(" | ",
                F.col("table_name"),
                F.lit("Columns: "), F.col("columns"),
                F.lit("Relations: "), F.col("relations")
            )
        )
    )

    # combined_text = (
    #     full_metadata_df
    #     .select(concat_ws("\n", collect_list("metadata_summary")).alias("schema_text"))
    #     .collect()[0]["schema_text"]
    # )
    combined_text_rdd = (
        full_metadata_df
        .select("metadata_summary")
        .rdd
        .map(lambda row: row["metadata_summary"])
    )

# Reduce on executors then collect just once
    combined_text = combined_text_rdd.reduce(lambda a, b: a + "\n" + b)
    # -------------------------------------------------------------------------
    # 5️⃣ Prepare LLM prompt
    # -------------------------------------------------------------------------
    prompt = """Given the following database schema and table relationships,
suggest potential Machine Learning use cases that can be built from this data.

Return the output strictly as a JSON array of objects with the following keys:
[
  {
    "use_case_name": "string",
    "description": "string",
    "associated_tables": "comma-separated table names",
    "explanation_columns": "comma-separated important columns"
  }
]
Now analyze this schema:
"""

    # -------------------------------------------------------------------------
    # 6️⃣ Check if query_model() exists in Spark
    # -------------------------------------------------------------------------
    functions_df = spark.sql("SHOW FUNCTIONS")
    function_names = [row.function for row in functions_df.collect()]
    query_model_available = any("query_model" in f for f in function_names)

    # -------------------------------------------------------------------------
    # 7️⃣ If query_model is available → run real LLM
    # -------------------------------------------------------------------------
    if query_model_available:
        schema_text_df = spark.createDataFrame([(combined_text,)], ["schema_text"])
        schema_text_df = schema_text_df.withColumn("prompt_col", F.lit(prompt))
        llm_json_df = schema_text_df.withColumn(
            "llm_json_response",
            expr(f"query_model('{model_id}', concat(prompt_col, schema_text))")
        )

        schema = ArrayType(
            StructType([
                StructField("use_case_name", StringType()),
                StructField("description", StringType()),
                StructField("associated_tables", StringType()),
                StructField("explanation_columns", StringType())
            ])
        )

        parsed_df = llm_json_df.withColumn(
            "parsed", F.from_json(F.col("llm_json_response"), schema)
        ).withColumn("use_case", F.explode("parsed"))

        final_df = parsed_df.select(
            F.col("use_case.use_case_name"),
            F.col("use_case.description"),
            F.col("use_case.associated_tables"),
            F.col("use_case.explanation_columns")
        )

        print("✅ AIDP LLM executed successfully.")
        return final_df

    # -------------------------------------------------------------------------
    # 8️⃣ Else → fallback to mock results for local dev
    # -------------------------------------------------------------------------
    else:
        print("⚠️ 'query_model' not found — returning mock data for local testing.")
        mock_data = [
            ("Customer Churn Prediction", "Predict customers likely to leave the service.", "customers", "customerid, churn, tenure, monthlycharges"),
            ("Fraud Detection", "Detect suspicious transactions.", "transactions", "transactionid, amount, timestamp"),
            ("Revenue Forecasting", "Forecast future revenue based on past performance.", "sales, customers", "date, amount, region"),
        ]
        return spark.createDataFrame(mock_data, ["use_case_name", "description", "associated_tables", "explanation_columns"])
