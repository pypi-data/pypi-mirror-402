-- Singular test: ensure no negative revenue
select
    order_id,
    gross_amount
from "memory"."main"."fct_orders"
where gross_amount < 0