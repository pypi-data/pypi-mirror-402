from .utils import get_env, get_table_info

# def load_latest_file_bronze(spark, data_base, schema, table, env=None):
def load_latest_parquet(spark, data_base, schema, table, env=None):
    """
    Carga el último archivo Parquet para la tabla especificada y retorna un DataFrame.
    
    Parámetros:
      spark (SparkSession): Sesión activa de Spark.
      data_base (str): Nombre de la base de datos.
      schema (str): Nombre del esquema.
      table (str): Nombre de la tabla.
      env (str, opcional): Entorno de ejecución (por ejemplo: 'dev', 'qa', 'prod').
                           Si no se proporciona, se obtiene usando get_env().
    
    Retorna:
      DataFrame de Spark cargado desde el archivo Parquet más reciente.
    """
    env = env or get_env()
    base_path = f"/Volumes/bronze/{data_base}_{schema}/{env}/{table}/"

    try:
        files = dbutils.fs.ls(base_path) # type: ignore

        parquet_files = [f for f in files if table in f.name]
        
        if not parquet_files:
            return None
        
        latest_file = sorted(parquet_files, key=lambda f: f.name, reverse=True)[0]
        df = spark.read.parquet(latest_file.path)
        return df
             
    except Exception as e:
        print("Error al procesar los archivos:", e)
        return None

    
def return_parquets_and_register_temp_views(spark, tables_load, verbose=False, env=None):
    """
    Carga dataframes a partir de un diccionario de definición de tablas y materializa vistas temporales.
    Retorna un diccionario con los dataframes.
    
    Parámetros:
        spark (SparkSession): Sesión activa de Spark.
        tables_load (dict): Diccionario que define las tablas a cargar y sus vistas temporales.
        verbose (bool): Si es True, imprime mensajes de estado durante la carga.
        env (str, opcional): Entorno de ejecución (por ejemplo: 'dev', 'qa', 'prod').
                             Si no se proporciona, se obtiene usando get_env().
                             
    Retorna:
        dict: Diccionario donde las claves son nombres completos de tablas y los valores son DataFrames.
    """
    dataframes = {}

    for data_base, schemas in tables_load.items():
        for schema, tables in schemas.items():
            for t in tables:
                table = t['table']
                view = t['view']

                # Cargar el dataframe usando la función que proveés
                df = load_latest_parquet(spark, data_base, schema, table, env)
                
                # Guardar en el diccionario
                key = f"{data_base}.{schema}.{table}"
                dataframes[key] = df

                # Materializar la vista (esto no necesita asignación en Python)
                try:
                    df.createOrReplaceTempView(view)
                    if verbose:
                        print(f'Tabla "{key}" cargada y vista "{view}" materializada')
                except Exception as e:
                    print(f"Error al materializar la vista '{view} tabla {key}': {e}")
                
    return dataframes


def parquets_register_temp_views(spark, tables_load, verbose=False, env=None):
    """
    Lee los últimos parquets y materializa vistas temporales en Spark. Sin retorna nada.
    Parámetros:
        spark (SparkSession): Sesión activa de Spark.
        tables_load (dict): Diccionario que define las tablas a cargar y sus vistas temporales.
            La estructura esperada del parámetro `tables_load` es un diccionario
            anidado con el siguiente formato:

                {
                    "<base_de_datos>": {
                        "<schema>": [
                            {
                                "table": "<nombre_tabla>",
                                "view": "<nombre_vista_temporal>"
                            },
                            ...
                        ]
                    },
                    ...
                }
            Ejemplo:
                tables_load = {
                    "bup": {
                        "bup": [
                            {"table": "naturalpersons", "view": "vw_naturalpersons"},
                            {"table": "maritalstatus", "view": "vw_maritalstatus"},
                            {"table": "genders", "view": "vw_genders"},
                            {"table": "legalpersons", "view": "vw_legalpersons"},
                            {"table": "phones", "view": "vw_phones"},
                            {"table": "emails", "view": "vw_emails"},
                            {"table": "addresses", "view": "vw_addresses"},
                            {"table": "persons", "view": "vw_persons"},
                            {"table": "administrativefreezeperiods", "view": "vw_administrativefreezeperiods"},
                            {"table": "fraudrisklevels", "view": "vw_fraudrisklevels"},
                        ],
                    },
                    "oraculo": {
                        "dbo": [
                            {"table": "ml_segmentacion", "view": "vw_segmentacion"},
                        ],
                    },
                    "timepro": {
                        "insudb": [
                            {"table": "logauth0user", "view": "vw_logauth0user"},
                            {"table": "benefitprogramadhesion", "view": "vw_benefitprogramadhesion"},
                        ],
                    },
                    "dwgssprotmp": {
                        "dwo": [
                            {"table": "int_dim_clientactive_bds", "view": "vw_int_dim_cliente_active"},
                        ],
                    },
                    "odscommon": {
                        "employee": [
                            {"table": "vw_active_employee", "view": "vw_active_employee"},
                        ],
                    },
                }
        verbose (bool): Si es True, imprime mensajes de estado durante la carga.
        env (str, opcional): Entorno de ejecución (por ejemplo: 'dev', 'qa', 'prod').
                             Si no se proporciona, se obtiene usando get_env().
    Retorna:
        None
    """
    for data_base, schemas in tables_load.items():
        for schema, tables in schemas.items():
            for t in tables:
                table = t['table']
                view = t['view']
                try:
                    df = load_latest_parquet(spark, data_base, schema, table, env)
                    df.createOrReplaceTempView(view)
                    if verbose:
                        print(f'Vista "{view}" materializada desde {data_base}.{schema}.{table}')
                except Exception as e:
                    print(f"Error al materializar la vista '{view}' desde {data_base}.{schema}.{table}: {e}")


def load_latest_excel(spark, source_file, env=None):
    
    """
    Carga el último archivo de Excel (aunque no tenga extensión visible) para la carpeta especificada
    y retorna un DataFrame.
    
    Parámetros:
      spark (SparkSession): Sesión activa de Spark.
      source_file (str): Nombre de la carpeta.
        env (str, opcional): Entorno de ejecución (por ejemplo: 'dev', 'qa', 'prod').
                            Si no se proporciona, se obtiene usando get_env().
    Retorna:
      DataFrame de Spark cargado desde el archivo Excel más reciente (en formato xls).
    """
    
    import pandas as pd
    
    env = env or get_env()
    base_path = f"/Volumes/bronze/excel/{env}/{source_file}/"
    print("Ruta base:", base_path)
    
    try:
        files = dbutils.fs.ls(base_path) # type: ignore
        print("Archivos encontrados:", [f.name for f in files])     
        excel_candidates = [f for f in files if f.isFile()]

        if not excel_candidates:
            print(f"No se encontraron archivos en la carpeta: {source_file}")
            return None
        
        latest_file = sorted(excel_candidates, key=lambda f: f.name, reverse=True)[0]
        
        file_path = latest_file.path.replace("dbfs:", "")

        pdf = pd.read_excel(file_path, header=0, engine='xlrd')
        
        return spark.createDataFrame(pdf)
    
    except Exception as e:
        return None


def return_excels_and_register_temp_views(spark, files_load, verbose=False, env=None):
    """
    Carga dataframes a partir de un diccionario de definición de excels y materializa vistas temporales.
    Retorna un diccionario con los dataframes.
    
    Parámetros:
        spark (SparkSession): Sesión activa de Spark.
        files_load (dict): Diccionario que define las tablas a cargar y sus vistas temporales.
            La estructura esperada del parámetro `files_load` es un diccionario
            anidado con el siguiente formato:

                {
                    "<Dominio>": {
                        "<SubDominio>": [
                            {
                                "file": "<nombre_archivo>",
                                "view": "<nombre_vista_temporal>"
                            },
                            ...
                        ]
                    },
                    ...
                }
            Ejemplo:
        verbose (bool): Si es True, imprime mensajes de estado durante la carga.
        env (str, opcional): Entorno de ejecución (por ejemplo: 'dev', 'qa', 'prod').
                             Si no se proporciona, se obtiene usando get_env().
    
    Retorna:
        dict: Diccionario donde las claves son nombres completos de tablas y los valores son DataFrames.
            Quedando las vistas materializadas en el entorno Spark.
    """
    dataframes = {}

    for domain, subdomain in files_load.items():
        for subdomain, tables in subdomain.items():
            for t in tables:
                file = t['file']
                view = t['view']

                # Cargar el dataframe usando la función que proveés
                source_file = f"{domain}/{subdomain}/{file}"
                df = load_latest_excel(spark, source_file, env)
                
                # Guardar en el diccionario
                key = f"{domain}.{subdomain}.{file}"
                dataframes[key] = df

                # Materializar la vista (esto no necesita asignación en Python)
                try:
                    df.createOrReplaceTempView(view)
                    if verbose:
                        print(f'El archivo "{key}" cargado y vista "{view}" materializada')
                except Exception as e:
                    print(f"Error al materializar la vista '{view} tabla {key}': {e}")
                
    return dataframes


def excels_register_temp_views(spark, files_load, verbose=False, env=None):
    """
    Lee los últimos archivos excels y materializa vistas temporales en Spark. Sin retorna nada.
    
    Parámetros:
        spark (SparkSession): Sesión activa de Spark.
        files_load (dict): Diccionario que define las tablas a cargar y sus vistas temporales.
            La estructura esperada del parámetro `files_load` es un diccionario
            anidado con el siguiente formato:

                {
                    "<Dominio>": {
                        "<SubDominio>": [
                            {
                                "file": "<nombre_archivo>",
                                "view": "<nombre_vista_temporal>"
                            },
                            ...
                        ]
                    },
                    ...
                }
            Ejemplo:
        verbose (bool): Si es True, imprime mensajes de estado durante la carga.
        env (str, opcional): Entorno de ejecución (por ejemplo: 'dev', 'qa', 'prod').
                             Si no se proporciona, se obtiene usando get_env().
    
    Retorna:
        Nada
    """

    for domain, subdomain in files_load.items():
        for subdomain, tables in subdomain.items():
            for t in tables:
                file = t['file']
                view = t['view']

                # Cargar el dataframe usando la función que proveés
                source_file = f"{domain}/{subdomain}/{file}"
                df = load_latest_excel(spark, source_file, env)
                
                # Guardar en el diccionario
                key = f"{domain}.{subdomain}.{file}"

                # Materializar la vista (esto no necesita asignación en Python)
                try:
                    df.createOrReplaceTempView(view)
                    if verbose:
                        print(f'El archivo "{key}" leido y vista "{view}" materializada')
                except Exception as e:
                    print(f"Error al materializar la vista '{view} tabla {key}': {e}")


def load_and_materialize_views(action, **kwargs):    
    actions_load_bronze = {
        # Todas las acciones aqui declaradas deberan devolver un diccionario de DataFrames
        # 'load_notebook': load_notebook,
        'return_parquets_and_register_temp_views': return_parquets_and_register_temp_views,
        'parquets_register_temp_views': parquets_register_temp_views,
        'return_excels_and_register_temp_views': return_excels_and_register_temp_views,
        'excels_register_temp_views': excels_register_temp_views,
        # ir agregando más acciones acá
    }
    results = {}
    func = actions_load_bronze.get(action)
    if func:
        results = func(**kwargs)
        # results[action] = result
    else:
        print(f"Acción '{action}' no está implementada.")
    return results


def save_table_to_delta(df, catalog, schema, table_name):
    """
    Guarda un DataFrame en formato Delta en la ubicación y tabla especificadas,
    sobrescribiendo los datos existentes y el esquema si es necesario.

    Parámetros:
      df (DataFrame): DataFrame de Spark que se desea guardar.
      db_name (str): Nombre del catálogo o base de datos destino.
      schema (str): Nombre del esquema, capa o entorno destino (ejemplo: 'silver', 'gold').
      table_name (str): Nombre de la tabla destino.

    Retorna:
      None

    Lógica:
      - Utiliza la función auxiliar 'get_table_info' para obtener el path
        de almacenamiento y el nombre completo de la tabla.
      - Escribe el DataFrame en formato Delta en la ruta especificada,
        sobrescribiendo cualquier dato y adaptando el esquema si es necesario.
      - Registra la tabla como tabla administrada en el metastore con el nombre completo.

    Notas:
      - El modo 'overwrite' reemplaza todos los datos existentes en la tabla.
      - La opción 'overwriteSchema' asegura que el esquema de la tabla se actualice si cambió.
      - Es necesario que la ruta y la tabla existan o sean accesibles en el entorno Spark.
      - Las opciones
        `.option("delta.columnMapping.mode", "nameMapping")` y `.option("delta.columnMapping.mode", "name")`
        permiten especificar el modo de mapeo de columnas para Delta Lake:
          - **"nameMapping"**: usa un mapeo explícito de columnas por nombre, útil para cambios de nombre o reordenamiento de columnas sin perder datos.
          - **"name"**: usa el nombre de columna directamente para el mapeo, opción recomendada cuando no se necesita trazabilidad de cambios en los nombres de columna, permite utilizar los acentos en el nombre de las columnas.
      - Si ambas opciones se usan al mismo tiempo, solo una tendrá efecto (se aplicará la última indicada).

    """
    dim_destino = get_table_info(catalog=catalog, schema=schema, table=table_name)
    (
        df.write
        .format("delta")
        .option("path", dim_destino["path"])
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .option("delta.columnMapping.mode", "nameMapping") \
        .option("delta.columnMapping.mode", "name") \
        .saveAsTable(dim_destino["full_table_name"])
    )
