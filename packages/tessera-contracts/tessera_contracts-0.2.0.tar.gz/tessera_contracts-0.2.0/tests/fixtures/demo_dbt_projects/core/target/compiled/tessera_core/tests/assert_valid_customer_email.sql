-- Singular test: ensure all customers have valid email format
select
    customer_id,
    email
from "memory"."main"."dim_customers"
where email not like '%@%.%'