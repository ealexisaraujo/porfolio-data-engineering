from datetime import datetime, timedelta
from airflow.models import Variable
from airflow.models import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.contrib.operators.snowflake_operator import SnowflakeOperator
import pandas as pd
from utils import get_data,data_processing
from datetime import datetime




default_arguments = {   'owner': 'alexisaraujo',
                        'email': 'me@alexisaraujo.com',
                        'retries':1 ,
                        'retry_delay':timedelta(minutes=5)}


with DAG('FOOTBAL_LEAGUES',
         default_args=default_arguments,
         description='Extracting Data Footbal League' ,
         start_date = datetime(2022, 9, 21),
         schedule_interval = None,
         tags=['tabla_espn'],
         catchup=False) as dag :


         params_info = Variable.get("feature_info", deserialize_json=True)
         df = pd.read_csv('/usr/local/airflow/df_ligas.csv')
         df_team = pd.read_csv('/usr/local/airflow/team_table.csv')

         def extract_info(df ,df_team ,**kwargs):

            df_data = data_processing(df)

            df_final = pd.merge(df_data,df_team,how='inner',on='EQUIPO')
            df_final = df_final[['ID_TEAM','EQUIPO', 'J', 'G', 'E', 'P', 'GF', 'GC', 'DIF', 'PTS', 'LIGA',
                'CREATED_AT']]

            df_final.to_csv('./premier_positions.csv',index=False)


         extract_data = PythonOperator(task_id='EXTRACT_FOTBALL_DATA',
                                    provide_context=True,
                                    python_callable=extract_info,
                                    op_kwargs={"df":df,"df_team":df_team})

         upload_stage = SnowflakeOperator(

                    task_id='upload_data_stage',
                    sql='./sql/upload_stage.sql',
                    snowflake_conn_id='demo_snowflake',
                    warehouse=params_info["DWH"],
                    database=params_info["DB"],
                    role=params_info["ROLE"],
                    params=params_info
                    )
         ingest_table = SnowflakeOperator(

                    task_id='ingest_table',
                    sql='./sql/upload_table.sql',
                    snowflake_conn_id='demo_snowflake',
                    warehouse=params_info["DWH"],
                    database=params_info["DB"],
                    role=params_info["ROLE"],
                    params=params_info
                    )

         extract_data >>  upload_stage >> ingest_table