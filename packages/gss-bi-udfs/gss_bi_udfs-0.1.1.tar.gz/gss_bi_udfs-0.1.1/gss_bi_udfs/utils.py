import os
from pyspark.sql.types import (IntegerType, LongType, ShortType, ByteType,
                               DecimalType, DoubleType, FloatType,
                               DateType, TimestampType, BooleanType, StringType)
from pyspark.sql.functions import lit, concat_ws, col
from pyspark.sql import DataFrame, Column


def get_env(default="dev"):
    """
    Obtiene el entorno de ejecución a partir de la variable de entorno ENV.
    Si no está definida, retorna el valor por defecto indicado.

    Parámetros:
    - default (str): entorno por defecto a utilizar si ENV no está definida.

    Retorna:
    - str: nombre del entorno de ejecución (por ejemplo: 'dev', 'qa', 'prod').
    """
    
    return os.getenv("ENV", default)

def get_env_catalog(catalog):
    """
    Genera el nombre del catálogo ajustado al environment.

    Parámetros:
      catalog (str): Nombre base del catálogo (ej. 'fi_comunes').

    Retorna:
      str: Nombre del catálogo ajustado al environment.
           Ejemplo: 'fi_comunes_dev' si ENV='dev'
                    'fi_comunes' si ENV='pro'
    """
    
    if get_env() == "pro":
        return catalog
    else:
        return f"{catalog}_{get_env()}"
    
    
def get_env_table_path(catalog, table_path):
    """
    Genera el path completo de una tabla incluyendo el sufijo de ambiente en el catálogo.

    Parámetros:
      catalog (str): Nombre base del catálogo (ej. 'fi_comunes').
      table_path (str): Path de la tabla incluyendo esquema y nombre (ej. 'silver.dim_afiliado').

    Retorna:
      str: Path completo de la tabla ajustado al environment.
           Ejemplo: 'fi_comunes_dev.silver.dim_afiliado' si ENV='dev'
                    'fi_comunes.silver.dim_afiliado' si ENV='pro'
    """

    # Concatena el catálogo modificado con el path de la tabla
    return f"{get_env_catalog(catalog)}.{table_path}"

def get_schema_root_location(spark, catalog, schema):
    """
    Obtiene la ruta física (RootLocation) de un esquema específico, considerando el catálogo ajustado al ambiente.

    Parámetros:
      catalog (str): Nombre base del catálogo (ej. 'fi_comunes').
      schema (str): Nombre del esquema dentro del catálogo (ej. 'silver').

    Retorna:
      str: Ruta física donde se almacenan los datos del esquema.
           Ejemplo: 's3://bucket/path/fi_comunes_dev/silver' si ENV='dev'
    
    Requiere:
      - La función get_env_catalog debe estar definida y retornar el nombre de catálogo ajustado al ambiente.
      - SparkSession activa y permisos para ejecutar `DESCRIBE SCHEMA EXTENDED`.

    Ejemplo:
      >>> get_schema_root_location("fi_comunes", "silver")
      's3://mi-bucket/datalake/fi_comunes_dev/silver'
    """
    cat = get_env_catalog(catalog)
    df = spark.sql(f"DESCRIBE SCHEMA EXTENDED {cat}.{schema}")
    return df.filter("database_description_item = 'RootLocation'") \
             .select("database_description_value") \
             .collect()[0][0]
             
def get_table_info(
    spark,
    *,
    full_table_name: str = None,
    catalog: str = None,
    schema: str = None,
    table: str = None
) -> dict:
    """
    Devuelve información de una tabla a partir de:
    - full_table_name (catalog.schema.table)
    o
    - catalog + schema + table
    """

    # -----------------------------
    # 1. Resolver inputs
    # -----------------------------
    if full_table_name:
        parts = full_table_name.split(".")
        if len(parts) != 3:
            raise ValueError(
                "full_table_name debe tener formato catalog.schema.table"
            )
        catalog, schema, table = parts

    elif catalog and schema and table:
        full_table_name = f"{catalog}.{schema}.{table}"

    else:
        raise ValueError(
            "Debe informar full_table_name o catalog + schema + table"
        )

    # -----------------------------
    # 2. Environment catalog
    # -----------------------------
    catalog_env = get_env_catalog(catalog)

    # -----------------------------
    # 3. Path físico
    # -----------------------------
    root_location = get_schema_root_location(spark, catalog, schema)
    path = f"{root_location.rstrip('/')}/{table}"

    # -----------------------------
    # 4. Metadata Spark (si existe)
    # -----------------------------
    info = {
        "catalog": catalog_env,
        "schema": schema,
        "table": table,
        "full_table_name": f"{catalog_env}.{schema}.{table}",
        "path": path,
        "exists": False,
        "provider": None,
        "table_type": None,
    }

    if spark.catalog.tableExists(info["full_table_name"]):
        info["exists"] = True

        desc = (
            spark.sql(f"DESCRIBE EXTENDED {info['full_table_name']}")
            .filter("col_name in ('Location', 'Provider', 'Type')")
            .collect()
        )

        for row in desc:
            if row.col_name == "Location":
                info["path"] = row.data_type
            elif row.col_name == "Provider":
                info["provider"] = row.data_type
            elif row.col_name == "Type":
                info["table_type"] = row.data_type

    return info


    
def get_default_value_by_type(dtype):
        """
        Devuelve "default" por tipo de dato para registros 'default/unknown'.
        Parámetros:
            - dtype: Tipo de dato (DataType) de PySpark.
        Retorna:
            - valor por defecto correspondiente al tipo de dato.
        """
        if isinstance(dtype, (IntegerType, LongType, ShortType, ByteType)):
            return lit(-999)
        if isinstance(dtype, (DecimalType, DoubleType, FloatType)):
            return lit(-999)
        if isinstance(dtype, (DateType, TimestampType)):
            return lit("1900-01-01").cast(dtype)
        if isinstance(dtype, BooleanType):
            return lit(False)
        if isinstance(dtype, StringType):
            return lit("N/A")
        return lit(None)
    

