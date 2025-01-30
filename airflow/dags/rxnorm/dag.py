from pathlib import Path
import pendulum

from sagerx import get_dataset, read_sql_file, get_sql_list, alert_slack_channel

from airflow.decorators import dag, task

from airflow.operators.python import get_current_context
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.hooks.postgres_hook import PostgresHook
from airflow.models import Variable

from common_dag_tasks import extract, transform, run_subprocess_command


@dag(
    schedule="0 0 10 * *",
    start_date=pendulum.datetime(2005, 1, 1),
    catchup=False,
)
def rxnorm():
    dag_id = "rxnorm"
    api_key = Variable.get("umls_api")
    ds_url = f"https://uts-ws.nlm.nih.gov/download?url=https://download.nlm.nih.gov/umls/kss/rxnorm/RxNorm_full_current.zip&apiKey={api_key}"

    extract_task = extract(dag_id, ds_url)

    # Task to load data into source db schema
    load = []
    ds_folder = Path("/opt/airflow/dags") / dag_id
    for sql in get_sql_list("load", ds_folder):
        sql_path = ds_folder / sql
        task_id = sql[:-4]
        load.append(
            PostgresOperator(
                task_id=task_id,
                postgres_conn_id="postgres_default",
                sql=read_sql_file(sql_path),
            )
        )

    # Task to transform data using dbt
    @task
    def transform():
        # WHY???? now there is a docker in docker depenedency
        # run_subprocess_command(['docker', 'exec', 'dbt', 'dbt', 'run', '--select', 'models/staging/rxnorm', 'models/intermediate/rxnorm'], cwd='/dbt/sagerx')
        run_subprocess_command(['dbt', 'run', '--select', 'models/staging/rxnorm', 'models/intermediate/rxnorm'], cwd='/dbt/sagerx')
        
    extract(get_st(get_tgt())) >> load >> transform()
    transform_task = transform(dag_id, models_subdir=['staging', 'intermediate'])

    #extract_task >> load >> transform_task

rxnorm()
