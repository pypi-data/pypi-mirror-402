
  
  create view "demo"."main"."stg_orders__dbt_tmp" as (
    -- Staging layer: clean and type raw orders

select
    order_id,
    customer_id,
    cast(order_date as date) as order_date,
    cast(amount as decimal(10, 2)) as amount,
    status
from "demo"."main"."raw_orders"
  );
