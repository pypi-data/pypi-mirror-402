from pyspark.sql import functions as F
from .io import save_table_to_delta
from .utils import get_table_info
from .transforms import add_hashid

def merge_scd2(
    spark,
    df_dim_src,
    table_name,
    business_keys,
    surrogate_key,
    eow_date="9999-12-31"
):
    """
    Aplica Slowly Changing Dimension Tipo 2 (SCD2) sobre una tabla Delta.

    El DataFrame de entrada (`df_dim_src`) debe representar el estado actual de la dimensión
    a nivel de negocio, con el MISMO esquema lógico que la tabla destino,
    excluyendo únicamente la PK física (surrogate key) del Data Warehouse.
    `df_dim_src` NO debe incluir la clave primaria física (surrogate key).
    Esta se genera internamente como un hash de (business_keys + valid_from).

    La lógica implementa versionado histórico de registros utilizando fechas de vigencia
    (valid_from, valid_to), manteniendo una única versión activa por entidad de negocio.

    CONCEPTOS CLAVE Y SUPUESTOS DEL MODELO
    -------------------------------------
    1. Clave de negocio (Business Keys):
       - El parámetro `business_keys` DEBE representar la clave de negocio que identifica
         unívocamente a la entidad (por ejemplo: nbranch, nproduct).
       - Esta clave NO debe cambiar en el tiempo.
       - El merge se realiza exclusivamente contra esta clave de negocio
         y contra el registro activo (valid_to = eow_date).

    2. Clave primaria física del Data Warehouse:
       - La dimensión DEBE tener una clave primaria física (surrogate key) propia del DW
         para identificar cada versión histórica del registro.
       - Esta PK física NO participa de la lógica de comparación ni del merge funcional,
         y su generación queda fuera del alcance de esta función.

    3. Columnas comparadas (detección de cambios):
       - La función compara TODAS las columnas del DataFrame de entrada
         EXCEPTO:
           - la clave de negocio (`business_keys`)
           - las columnas de vigencia (`valid_from`, `valid_to`)
       - Si cualquiera de las columnas comparadas cambia, se genera una nueva versión
         del registro (SCD Tipo 2).
       - Esto implica que cualquier nueva columna agregada al esquema será
         automáticamente considerada para versionado.

       IMPORTANTE:
       - Por este motivo, se recomienda que el DataFrame NO incluya columnas técnicas
         o volátiles (timestamps de carga, ids de proceso, metadatos, etc.),
         ya que provocarían versionado innecesario.

       - El DataFrame de entrada PUEDE incluir las columnas `valid_from` y `valid_to`;
         en caso de existir, serán ignoradas para la detección de cambios y
         recalculadas internamente por la función.

    4. Manejo de fechas de vigencia:
       - valid_from: DATE inclusiva
       - valid_to:    DATE inclusiva
       - El registro activo siempre tiene valid_to = eow_date (por defecto 9999-12-31).
       - Ante un cambio:
           * la versión anterior se cierra con valid_to = current_date() - 1
           * la nueva versión se inserta con valid_from = current_date()
       - Esto garantiza que no existan solapamientos de vigencia.

       - Si el DataFrame de entrada no contiene `valid_from` y `valid_to`,
         la función las generará automáticamente durante la carga inicial
         o incremental.

    5. Carga inicial:
       - Si la tabla destino no existe, se realiza un full load inicial,
         asignando valid_from = '1900-01-01' y valid_to = eow_date
         a todos los registros.

    PARÁMETROS
    ----------
    spark : SparkSession
        SparkSession activo.
    df_dim_src : DataFrame
        DataFrame de Spark que contiene los datos a mergear.
        Debe incluir TODAS las columnas de negocio de la dimensión
        (clave(s) de negocio + atributos versionables),
        con el mismo esquema lógico que la tabla destino.
        NO debe incluir la clave primaria física (surrogate key).
    table_name : str
        Nombre completo (catalogo.esquema.tabla) de la tabla Delta destino. 
    business_keys : str or list[str]
        Nombre(s) de la(s) columna(s) que representa(n) la clave de negocio.
        Puede ser una clave simple (str) o compuesta (lista de str).
    surrogate_key : str
        Nombre de la clave primaria física (surrogate key) de la dimensión.
        Se genera internamente como un hash de (business_keys + valid_from).
    eow_date : str, opcional
        Fecha de fin de vigencia para registros activos.
        Por defecto: '9999-12-31'.

    RETORNO
    -------
    None
        La función ejecuta el merge directamente sobre la tabla Delta.
    """

    # Normalize business_keys to a list (support single column or composite key)
    if isinstance(business_keys, str):
        business_keys = [business_keys]

    missing_bk = [c for c in business_keys if c not in df_dim_src.columns]
    if missing_bk:
        raise ValueError(f"Columnas de business key inexistentes en df_dim_src: {missing_bk}")

    exclude_cols = set(business_keys) | {"valid_from", "valid_to"}
    compare_cols = [c for c in df_dim_src.columns if c not in exclude_cols]

    info_table = get_table_info(spark,full_table_name=table_name)

    if not spark.catalog.tableExists(table_name):
        df_nov = (
            df_dim_src
            .withColumn("valid_from", F.to_date(F.lit("1900-01-01")))
            .withColumn("valid_to",   F.to_date(F.lit(eow_date)))
        )
        pk_cols = business_keys + ["valid_from"]
        df_nov = add_hashid(df_nov, pk_cols, surrogate_key)
        
        save_table_to_delta(spark, df_nov, info_table["catalog"], info_table["schema"], info_table["table"])
        df_nov.write \
            .format("delta") \
            .mode("overwrite") \
            .option("overwriteSchema", "true") \
            .saveAsTable(table_name)
        print(f"[FULL LOAD] {table_name} creado con SCD-2")
        return

    df_nov = (
        df_dim_src
        .withColumn("valid_from", F.current_date().cast("date"))
        .withColumn("valid_to",   F.to_date(F.lit(eow_date)))
    )
    pk_cols = business_keys + ["valid_from"]
    df_nov = add_hashid(df_nov, pk_cols, surrogate_key)

    delta_tgt = info_table["full_table_name"]
    bk_cond = " AND ".join([f"t.{k} = s.{k}" for k in business_keys])
    merge_cond = f"{bk_cond} AND t.valid_to = date('{eow_date}')"
    t_hash = "xxhash64(concat_ws('', " + ", ".join(f"t.{c}" for c in compare_cols) + "))"
    s_hash = "xxhash64(concat_ws('', " + ", ".join(f"s.{c}" for c in compare_cols) + "))"
    diff_cond = f"{t_hash} <> {s_hash}"

    (delta_tgt.alias("t")
        .merge(df_nov.alias("s"), merge_cond)
        .whenMatchedUpdate(
            condition=diff_cond,
            set={"valid_to": "date_sub(current_date(), 1)"}
        )
        .whenNotMatchedInsertAll()
        .whenNotMatchedBySourceUpdate(
            condition=f"t.valid_to = date('{eow_date}')",
            set={"valid_to": "date_sub(current_date(), 1)"}
        )
        .execute()
    )

    closed_count = delta_tgt.toDF() \
        .filter(F.col("valid_to") == F.date_sub(F.current_date(), 1)) \
        .count()
    if closed_count > 0:
        print(f"Se cerraron {closed_count} versiones en {table_name}")

    t_active = (
        delta_tgt.toDF()
        .filter(F.col("valid_to") == F.to_date(F.lit(eow_date)))
    )
    join_conds = [F.col(f"s.{k}") == F.col(f"t.{k}") for k in business_keys] + [
        F.col(f"s.{c}") == F.col(f"t.{c}") for c in compare_cols
    ]
    df_to_app = df_nov.alias("s").join(
        t_active.alias("t"), on=join_conds, how="left_anti"
    )

    new_count = df_to_app.limit(1).count()
    if new_count > 0:
        df_to_app.write \
            .format("delta") \
            .mode("append") \
            .saveAsTable(table_name)
        print(f"Se insertaron nuevas versiones en {table_name}")
    else:
        print(f"No hay nuevas versiones para {table_name}")