-- Fact table: orders with customer info

select
    o.order_id,
    o.customer_id,
    c.customer_name,
    c.email as customer_email,
    o.order_date,
    o.amount,
    o.status,
    -- Derived fields
    case when o.status = 'completed' then o.amount else 0 end as revenue
from "demo"."main"."stg_orders" o
left join "demo"."main"."stg_customers" c on o.customer_id = c.customer_id