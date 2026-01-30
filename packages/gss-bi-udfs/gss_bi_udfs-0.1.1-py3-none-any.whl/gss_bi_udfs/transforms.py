from pyspark.sql import DataFrame
from pyspark.sql.functions import xxhash64
from pyspark.sql.functions import concat_ws, col


from .utils import get_default_value_by_type

def add_hashid(
        df: DataFrame,
        columns: list[str],
        new_col_name: str = "hashid"
    ) -> DataFrame:
        """
        Agrega una columna hash (PK) a partir de la concatenación de columnas
        y reordena el DataFrame dejando el hash como primera columna.

        Parametros:
            df: DataFrame de Spark de entrada
            columns: Lista de columnas a concatenar
            new_col_name: Nombre de la columna hash (default: hashid)
            
        Retorna:
            DataFrame con hash agregado
        """

        if not columns:
            raise ValueError("La lista de columnas no puede estar vacía")

        # Concatenación segura
        concatenated = concat_ws("|", *[col(c).cast("string") for c in columns])

        # Hash rápido y determinístico (ideal para PK técnica)
        df_with_hash = df.withColumn(new_col_name, xxhash64(concatenated))

        # Reordenar columnas
        original_cols = [c for c in df.columns if c != new_col_name]
        new_cols = [new_col_name] + original_cols

        return df_with_hash.select(*new_cols)
    

def get_default_record(spark, df: DataFrame) -> DataFrame:
    """
    Crea un DataFrame con un único registro de valores por defecto según el esquema de df:
    Parámetros:
        spark: SparkSession activo.
        df (DataFrame): DataFrame de Spark del cual se tomará el esquema.
        
    Retorna:
        DataFrame: DataFrame con un único registro con valores por defecto.
    """
    defaults = {}
    for field in df.schema.fields:
        defaults[field.name] = get_default_value_by_type(field.dataType)
    
    return spark.createDataFrame([defaults], schema=df.schema)