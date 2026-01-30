-- Singular test: ensure orders have at least one item
select
    o.order_id
from "memory"."main"."fct_orders" o
left join "memory"."main"."int_order_items_enriched" oi on o.order_id = oi.order_id
where oi.order_item_id is null