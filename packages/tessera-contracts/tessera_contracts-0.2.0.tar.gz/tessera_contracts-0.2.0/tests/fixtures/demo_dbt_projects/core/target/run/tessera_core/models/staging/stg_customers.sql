
  
  create view "memory"."main"."stg_customers__dbt_tmp" as (
    with source as (
    select * from "memory"."main"."raw_customers"
)

select
    customer_id,
    email,
    first_name,
    last_name,
    first_name || ' ' || last_name as full_name,
    cast(created_at as date) as created_at,
    country,
    segment,
    current_timestamp as _loaded_at
from source
  );
