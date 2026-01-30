-- Staging layer: clean and type raw customers

select
    customer_id,
    customer_name,
    email,
    cast(created_at as date) as created_at
from "demo"."main"."raw_customers"