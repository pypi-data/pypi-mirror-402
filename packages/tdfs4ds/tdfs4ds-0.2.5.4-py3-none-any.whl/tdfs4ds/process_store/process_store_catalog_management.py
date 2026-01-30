import teradataml as tdml
import tdfs4ds
from tdfs4ds.utils.query_management import execute_query,execute_query_wrapper
from tdfs4ds import logger_safe


def upgrade_process_catalog():

    # Step 1: Create a new table with the desired structure
    query_1 = f"""
    CREATE MULTISET TABLE {tdfs4ds.SCHEMA}.{tdfs4ds.PROCESS_CATALOG_NAME}_NEW ,FALLBACK ,
         NO BEFORE JOURNAL,
         NO AFTER JOURNAL,
         CHECKSUM = DEFAULT,
         DEFAULT MERGEBLOCKRATIO,
         MAP = TD_MAP1
         (
          PROCESS_ID VARCHAR(36) CHARACTER SET LATIN NOT CASESPECIFIC NOT NULL,
          PROCESS_TYPE VARCHAR(255) CHARACTER SET LATIN NOT CASESPECIFIC NOT NULL,
          VIEW_NAME VARCHAR(255) CHARACTER SET LATIN NOT CASESPECIFIC,
          --ENTITY_ID JSON(32000) CHARACTER SET LATIN,
          ENTITY_ID VARCHAR(255) CHARACTER SET LATIN NOT CASESPECIFIC NOT NULL,
          ENTITY_NULL_SUBSTITUTE JSON(32000) CHARACTER SET LATIN,  -- New column added here
          FEATURE_NAMES VARCHAR(1024) CHARACTER SET LATIN NOT CASESPECIFIC,
          FEATURE_VERSION VARCHAR(255) CHARACTER SET LATIN NOT CASESPECIFIC,
          DATA_DOMAIN VARCHAR(255) CHARACTER SET LATIN NOT CASESPECIFIC NOT NULL,
          METADATA JSON(32000) CHARACTER SET LATIN,
          ValidStart TIMESTAMP(0) WITH TIME ZONE NOT NULL,
          ValidEnd TIMESTAMP(0) WITH TIME ZONE NOT NULL,
          PERIOD FOR ValidPeriod  (ValidStart, ValidEnd) AS VALIDTIME)
    PRIMARY INDEX ( PROCESS_ID )
    INDEX ( PROCESS_TYPE )
    """

    # Step 2: Copy the data from the old table to the new table, filling ENTITY_NULL_SUBSTITUTE with an empty JSON object
    query_2 = f"""NONSEQUENCED VALIDTIME INSERT INTO {tdfs4ds.SCHEMA}.{tdfs4ds.PROCESS_CATALOG_NAME}_NEW 
    (PROCESS_ID, PROCESS_TYPE, VIEW_NAME, ENTITY_ID, ENTITY_NULL_SUBSTITUTE, FEATURE_NAMES, FEATURE_VERSION, DATA_DOMAIN, METADATA, ValidStart, ValidEnd)
    SELECT PROCESS_ID, PROCESS_TYPE, VIEW_NAME, ENTITY_ID, '{{}}', FEATURE_NAMES, FEATURE_VERSION, DATA_DOMAIN, METADATA, ValidStart, ValidEnd
    FROM ADLSLSEMEA_EFS_DEMO.FS_PROCESS_CATALOG;
    """

    # Step 3: Drop the old table
    query_3 = f"""RENAME TABLE {tdfs4ds.SCHEMA}.{tdfs4ds.PROCESS_CATALOG_NAME} TO {tdfs4ds.SCHEMA}.{tdfs4ds.PROCESS_CATALOG_NAME}_OLD;"""

    # Step 4: Rename the new table to the old table's name
    query_4 = f"""RENAME TABLE {tdfs4ds.SCHEMA}.{tdfs4ds.PROCESS_CATALOG_NAME}_NEW TO {tdfs4ds.SCHEMA}.{tdfs4ds.PROCESS_CATALOG_NAME};"""

    logger_safe('info', f'creation of the {tdfs4ds.SCHEMA}.{tdfs4ds.PROCESS_CATALOG_NAME}_NEW table')
    tdml.execute_sql(query_1)
    logger_safe('info', f'insert existing processes from {tdfs4ds.SCHEMA}.{tdfs4ds.PROCESS_CATALOG_NAME} to {tdfs4ds.SCHEMA}.{tdfs4ds.PROCESS_CATALOG_NAME}_NEW')
    tdml.execute_sql(query_2)
    logger_safe('info', f'rename {tdfs4ds.SCHEMA}.{tdfs4ds.PROCESS_CATALOG_NAME} to {tdfs4ds.SCHEMA}.{tdfs4ds.PROCESS_CATALOG_NAME}_OLD')
    tdml.execute_sql(query_3)
    logger_safe('info', f'rename {tdfs4ds.SCHEMA}.{tdfs4ds.PROCESS_CATALOG_NAME}_NEW to {tdfs4ds.SCHEMA}.{tdfs4ds.PROCESS_CATALOG_NAME}')
    tdml.execute_sql(query_4)

@execute_query_wrapper
def process_store_catalog_view_creation():
     """
     Constructs SQL queries to replace views related to the process store catalog.

     This function generates two SQL queries:

     1. A query to replace a view in the process store catalog with the content
        of the process catalog table. The query uses the `REPLACE VIEW` statement
        and locks rows for access during execution.

     2. A query to replace a view that contains split features from the process catalog
        table. This query utilizes a text processing function (`NGramSplitter`) to extract
        n-grams from a specified text column and creates a view based on the processed data.

     Returns:
         tuple: A pair of SQL query strings:
             - `query_1`: SQL to replace the primary process catalog view.
             - `query_2`: SQL to replace the split features view with processed data.
     """

     query_1 = f"""
        REPLACE VIEW {tdfs4ds.SCHEMA}.{tdfs4ds.PROCESS_CATALOG_NAME_VIEW} AS
        LOCK ROW FOR ACCESS
        CURRENT VALIDTIME
        SELECT 
        A.PROCESS_ID ,
        A.PROCESS_TYPE ,
        A.VIEW_NAME ,
        A.ENTITY_ID ,
        A.ENTITY_NULL_SUBSTITUTE ,
        A.FEATURE_NAMES ,
        A.FEATURE_VERSION AS PROCESS_VERSION,
        A.DATA_DOMAIN,
        A.METADATA,
        B.FOR_PRIMARY_INDEX,
        CASE WHEN B.FOR_DATA_PARTITIONING IS NULL THEN '' ELSE B.FOR_DATA_PARTITIONING END AS FOR_DATA_PARTITIONING,
        D.DATABASE_NAME AS FILTER_DATABASE_NAME,
        D.VIEW_NAME AS FILTER_VIEW_NAME,
        D.TABLE_NAME AS FILTER_TABLE_NAME
    FROM {tdfs4ds.SCHEMA}.{tdfs4ds.PROCESS_CATALOG_NAME} A
    LEFT JOIN {tdfs4ds.SCHEMA}.{tdfs4ds.DATA_DISTRIBUTION_NAME} B
    ON A.PROCESS_ID = B.PROCESS_ID
    LEFT JOIN {tdfs4ds.SCHEMA}.{tdfs4ds.FILTER_MANAGER_NAME} D
    ON A.PROCESS_ID = D.PROCESS_ID
    """

     query_2 = f"""
    REPLACE VIEW {tdfs4ds.SCHEMA}.{tdfs4ds.PROCESS_CATALOG_NAME_VIEW_FEATURE_SPLIT} AS
    LOCK ROW FOR ACCESS
    SELECT
        PROCESS_ID,
        PROCESS_TYPE,
        VIEW_NAME,
        ENTITY_ID,
        ENTITY_NULL_SUBSTITUTE,
        NGRAM AS FEATURE_NAME,
        PROCESS_VERSION,
        DATA_DOMAIN,
        METADATA,
        FOR_PRIMARY_INDEX,
        FOR_DATA_PARTITIONING,
        FILTER_DATABASE_NAME,
        FILTER_VIEW_NAME,
        FILTER_TABLE_NAME
    FROM NGramSplitter (
        ON (
        SELECT
        *
        FROM {tdfs4ds.SCHEMA}.{tdfs4ds.PROCESS_CATALOG_NAME_VIEW}
        ) as paragraphs_input
        USING
            TextColumn ('FEATURE_NAMES')
            ConvertToLowerCase ('false')
            Grams ('1')
            Delimiter(',')
    ) AS dt
    """
     return [query_1, query_2]
def process_store_catalog_creation(if_exists='replace', comment='this table is a process catalog'):
    """
    Create or replace a feature store catalog table in Teradata database.

    This function creates a catalog table in the specified schema of the Teradata database.
    The catalog table is used to store information about features, including their names, associated tables, databases, validity periods, etc.

    Parameters:
    - if_exists (str, optional): Specifies the behavior if the catalog table already exists.
      Default is 'replace', which means the existing table will be replaced.
    - comment (str, optional): A comment to describe the catalog table. Default is 'this table is a process catalog'.

    Returns:
    str: The name of the created or replaced catalog table.

    Notes:
    - The schema in which the catalog table will be created should be specified separately.
    - If the catalog table already exists and if_exists is set to 'replace', the existing table will be dropped and recreated.
    - This function also creates a secondary index on the 'PROCESS_TYPE' column for faster querying.
    - The catalog table structure includes columns for process ID, process type, view name, entity ID, feature names,
      feature version, data domain, metadata, and validity period.
    - This function relies on external global variables and configurations like 'tdfs4ds' and 'tdml' which should be set
      in the environment.
    - It also depends on an 'execute_query' function for executing SQL queries.

    Dependencies:
    - 'tdfs4ds' global variables for schema and table name.
    - 'tdml' for displaying SQL queries (if configured).
    - 'execute_query' for executing SQL queries.
    """

    # SQL query to create the catalog table
    query = f"""
    CREATE MULTISET TABLE {tdfs4ds.SCHEMA}.{tdfs4ds.PROCESS_CATALOG_NAME},
            FALLBACK,
            NO BEFORE JOURNAL,
            NO AFTER JOURNAL,
            CHECKSUM = DEFAULT,
            DEFAULT MERGEBLOCKRATIO,
            MAP = TD_MAP1
            (

                PROCESS_ID VARCHAR(36) NOT NULL,
                PROCESS_TYPE VARCHAR(255) CHARACTER SET LATIN NOT CASESPECIFIC NOT NULL,
                VIEW_NAME   VARCHAR(255) CHARACTER SET LATIN NOT CASESPECIFIC,
                --ENTITY_ID JSON(32000) CHARACTER SET LATIN,
                ENTITY_ID VARCHAR(255) CHARACTER SET LATIN NOT CASESPECIFIC NOT NULL,
                ENTITY_NULL_SUBSTITUTE JSON(32000),
                FEATURE_NAMES VARCHAR(1024) CHARACTER SET LATIN NOT CASESPECIFIC,
                FEATURE_VERSION VARCHAR(255) CHARACTER SET LATIN NOT CASESPECIFIC,
                DATA_DOMAIN VARCHAR(255) CHARACTER SET LATIN NOT CASESPECIFIC NOT NULL,
                METADATA JSON(32000),
                ValidStart TIMESTAMP(0) WITH TIME ZONE NOT NULL,
                ValidEnd TIMESTAMP(0) WITH TIME ZONE NOT NULL,
                PERIOD FOR ValidPeriod  (ValidStart, ValidEnd) AS VALIDTIME
            )
            PRIMARY INDEX (PROCESS_ID);
    """

    # SQL query to create a secondary index on the feature name
    query2 = f"CREATE INDEX (PROCESS_TYPE) ON {tdfs4ds.SCHEMA}.{tdfs4ds.PROCESS_CATALOG_NAME};"

    # SQL query to comment the table
    query3 = f"COMMENT ON TABLE {tdfs4ds.SCHEMA}.{tdfs4ds.PROCESS_CATALOG_NAME} IS '{comment}'"

    if tdfs4ds.DATA_DISTRIBUTION_TEMPORAL:
        query4 = f"""
        CREATE MULTISET TABLE {tdfs4ds.SCHEMA}.{tdfs4ds.DATA_DISTRIBUTION_NAME},
                FALLBACK,
                NO BEFORE JOURNAL,
                NO AFTER JOURNAL,
                CHECKSUM = DEFAULT,
                DEFAULT MERGEBLOCKRATIO,
                MAP = TD_MAP1
                (
                    PROCESS_ID VARCHAR(36) NOT NULL,
                    FOR_PRIMARY_INDEX VARCHAR(2048),
                    FOR_DATA_PARTITIONING VARCHAR(32000),
                    ValidStart TIMESTAMP(0) WITH TIME ZONE NOT NULL,
                    ValidEnd TIMESTAMP(0) WITH TIME ZONE NOT NULL,
                    PERIOD FOR ValidPeriod  (ValidStart, ValidEnd) AS VALIDTIME
                )
                PRIMARY INDEX (PROCESS_ID);
        """
    else:
        query4 = f"""
        CREATE MULTISET TABLE {tdfs4ds.SCHEMA}.{tdfs4ds.DATA_DISTRIBUTION_NAME},
                FALLBACK,
                NO BEFORE JOURNAL,
                NO AFTER JOURNAL,
                CHECKSUM = DEFAULT,
                DEFAULT MERGEBLOCKRATIO,
                MAP = TD_MAP1
                (
                    PROCESS_ID VARCHAR(36) NOT NULL,
                    FOR_PRIMARY_INDEX VARCHAR(2048),
                    FOR_DATA_PARTITIONING VARCHAR(32000)
                )
                PRIMARY INDEX (PROCESS_ID);
        """

    # SQL query to comment the table
    query5 = f"COMMENT ON TABLE {tdfs4ds.SCHEMA}.{tdfs4ds.DATA_DISTRIBUTION_NAME} IS 'DESCRIBES THE DATA DISTRIBUTION OF THE PROCESSES'"

    query6 = f"""
    CREATE MULTISET TABLE {tdfs4ds.SCHEMA}.{tdfs4ds.FILTER_MANAGER_NAME},
            FALLBACK,
            NO BEFORE JOURNAL,
            NO AFTER JOURNAL,
            CHECKSUM = DEFAULT,
            DEFAULT MERGEBLOCKRATIO,
            MAP = TD_MAP1
            (

                PROCESS_ID VARCHAR(36) NOT NULL,
                DATABASE_NAME VARCHAR(2048),
                VIEW_NAME VARCHAR(2048),
                TABLE_NAME VARCHAR(2048),
                ValidStart TIMESTAMP(0) WITH TIME ZONE NOT NULL,
                ValidEnd TIMESTAMP(0) WITH TIME ZONE NOT NULL,
                PERIOD FOR ValidPeriod  (ValidStart, ValidEnd) AS VALIDTIME
            )
            PRIMARY INDEX (PROCESS_ID);
    """

    # SQL query to comment the table
    query7 = f"COMMENT ON TABLE {tdfs4ds.SCHEMA}.{tdfs4ds.FILTER_MANAGER_NAME} IS 'LIST THE FILTER MANAGER ATTACHED TO THE PROCESSES'"
    try:
        # Attempt to execute the create table query
        execute_query(query)
        if tdml.display.print_sqlmr_query:
            print(query)
        logger_safe('info', f'TABLE {tdfs4ds.SCHEMA}.{tdfs4ds.PROCESS_CATALOG_NAME} has been created')
        execute_query(query3)
    except Exception as e:
        # If the table already exists and if_exists is set to 'replace', drop the table and recreate it
        logger_safe('error', str(e).split('\n')[0])
        if str(e).split('\n')[0].endswith('already exists.') and (if_exists == 'replace'):
            execute_query(f'DROP TABLE  {tdfs4ds.SCHEMA}.{tdfs4ds.PROCESS_CATALOG_NAME}')
            logger_safe('info', f'TABLE {tdfs4ds.SCHEMA}.{tdfs4ds.PROCESS_CATALOG_NAME} has been dropped')
            try:
                # Attempt to recreate the table after dropping it
                execute_query(query)
                logger_safe('info', f'TABLE {tdfs4ds.SCHEMA}.{tdfs4ds.PROCESS_CATALOG_NAME} has been re-created')
                if tdml.display.print_sqlmr_query:
                    print(query)
                execute_query(query3)
            except Exception as e:
                logger_safe('error', str(e).split('\n')[0])

    try:
        # Attempt to execute the create table query
        execute_query(query4)
        if tdml.display.print_sqlmr_query:
            print(query4)
        logger_safe('info', f'TABLE {tdfs4ds.SCHEMA}.{tdfs4ds.DATA_DISTRIBUTION_NAME} has been created')
        execute_query(query5)
    except Exception as e:
        # If the table already exists and if_exists is set to 'replace', drop the table and recreate it
        logger_safe('error', str(e).split('\n')[0])
        if str(e).split('\n')[0].endswith('already exists.') and (if_exists == 'replace'):
            execute_query(f'DROP TABLE  {tdfs4ds.SCHEMA}.{tdfs4ds.DATA_DISTRIBUTION_NAME}')
            logger_safe('info', f'TABLE {tdfs4ds.SCHEMA}.{tdfs4ds.DATA_DISTRIBUTION_NAME} has been dropped')
            try:
                # Attempt to recreate the table after dropping it
                execute_query(query4)
                logger_safe('info', f'TABLE {tdfs4ds.SCHEMA}.{tdfs4ds.DATA_DISTRIBUTION_NAME} has been re-created')
                if tdml.display.print_sqlmr_query:
                    print(query4)
                execute_query(query5)
            except Exception as e:
                logger_safe('error', str(e).split('\n')[0])

    try:
        # Attempt to execute the create table query
        execute_query(query6)
        if tdml.display.print_sqlmr_query:
            print(query6)
        logger_safe('info', f'TABLE {tdfs4ds.SCHEMA}.{tdfs4ds.FILTER_MANAGER_NAME} has been created')
        execute_query(query7)
    except Exception as e:
        # If the table already exists and if_exists is set to 'replace', drop the table and recreate it
        logger_safe('error', str(e).split('\n')[0])
        if str(e).split('\n')[0].endswith('already exists.') and (if_exists == 'replace'):
            execute_query(f'DROP TABLE  {tdfs4ds.SCHEMA}.{tdfs4ds.FILTER_MANAGER_NAME}')
            logger_safe('info', f'TABLE {tdfs4ds.SCHEMA}.{tdfs4ds.FILTER_MANAGER_NAME} has been dropped')
            try:
                # Attempt to recreate the table after dropping it
                execute_query(query6)
                logger_safe('info', f'TABLE {tdfs4ds.SCHEMA}.{tdfs4ds.FILTER_MANAGER_NAME} has been re-created')
                if tdml.display.print_sqlmr_query:
                    print(query6)
                execute_query(query7)
            except Exception as e:
                logger_safe('error', str(e).split('\n')[0])

    try:
        # Attempt to create the secondary index
        execute_query(query2)
        if tdml.display.print_sqlmr_query:
            print(query)
        logger_safe('info', f'SECONDARY INDEX ON TABLE {tdfs4ds.SCHEMA}.{tdfs4ds.PROCESS_CATALOG_NAME} has been created')
    except Exception as e:
        logger_safe('error', str(e).split('\n')[0])

    return tdfs4ds.PROCESS_CATALOG_NAME, tdfs4ds.DATA_DISTRIBUTION_NAME, tdfs4ds.FILTER_MANAGER_NAME

def get_process_info(process_id: str) -> dict:
    """
    Retrieve process information including SQL and columns from the process catalog.

    Args:
        process_id (str): The unique identifier of the process.
    Returns:
        dict: A dictionary containing process SQL and columns.
    """
    # Retrieve process SQL and columns
    process_catalog = tdfs4ds.process_catalog()
    try:
        process_info = process_catalog[process_catalog['PROCESS_ID'] == process_id].to_pandas().to_dict(orient='records')[0]
        process_info['ENTITY_COLUMNS']  = process_info['ENTITY_ID'].split(',')
        process_info['FEATURE_COLUMNS'] = process_info['FEATURE_NAMES'].split(',')
    except Exception as e:
        logger_safe('error', f"Error retrieving process info: {e}")
        return None
    
    # get the SQL query:
    if process_info:
        process_sql = tdfs4ds.utils.lineage.get_ddl(
            view_name = process_info['VIEW_NAME'].split('.')[1],
            schema_name = process_info['VIEW_NAME'].split('.')[0],
            object_type='view'
            )
        process_info['PROCESS_SQL'] = process_sql

    # retrieve feature documentation
    from tdfs4ds.genai.documentation import retrieve_documentation, retrieve_explain_documentation

    try:
        documentation = retrieve_documentation(process_id)
        process_info['DOCUMENTED_SQL']                 = documentation['DOCUMENTED_SQL']
        process_info['DOCUMENTED_ENTITY_COLUMNS']      = documentation['DOCUMENTED_ENTITY_COLUMNS']
        process_info['DOCUMENTED_FEATURE_COLUMNS']     = documentation['DOCUMENTED_FEATURE_COLUMNS']
        process_info['ENTITY_DESCRIPTION']             = documentation['ENTITY_DESCRIPTION']
        logger_safe('info', f"Successfully retrieved documentation for process_id {process_id}")
    except Exception as e:
        logger_safe('error', f"Error retrieving documentation: {e}")

    try:
        explain_documentation = retrieve_explain_documentation(process_id)
        process_info['EXPLAIN_ANALYSIS']               = explain_documentation['EXPLAIN_ANALYSIS']
        process_info['OPTIMIZATION_SCORE']             = explain_documentation['OPTIMIZATION_SCORE']
        process_info['EXPLAIN_WARNINGS']               = explain_documentation['EXPLAIN_WARNINGS']
        process_info['EXPLAIN_RECOMMENDATIONS']        = explain_documentation['EXPLAIN_RECOMMENDATIONS']
        logger_safe('info', f"Successfully retrieved explanation for process_id {process_id}")
    except Exception as e:
        logger_safe('error', f"Error retrieving explanation: {e}")  

    return process_info