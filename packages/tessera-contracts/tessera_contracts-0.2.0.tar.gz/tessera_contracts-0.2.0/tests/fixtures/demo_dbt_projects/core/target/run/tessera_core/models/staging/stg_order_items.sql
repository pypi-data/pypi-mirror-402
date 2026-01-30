
  
  create view "memory"."main"."stg_order_items__dbt_tmp" as (
    with source as (
    select * from "memory"."main"."raw_order_items"
)

select
    order_item_id,
    order_id,
    product_id,
    quantity,
    unit_price,
    quantity * unit_price as line_total,
    current_timestamp as _loaded_at
from source
  );
