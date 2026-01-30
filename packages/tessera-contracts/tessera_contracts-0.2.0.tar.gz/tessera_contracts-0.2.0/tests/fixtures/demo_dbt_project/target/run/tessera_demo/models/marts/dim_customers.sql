
  
  create view "demo"."main"."dim_customers__dbt_tmp" as (
    -- Dimension table: customer summary

select
    c.customer_id,
    c.customer_name,
    c.email,
    c.created_at,
    count(o.order_id) as total_orders,
    coalesce(sum(case when o.status = 'completed' then o.amount else 0 end), 0) as lifetime_revenue
from "demo"."main"."stg_customers" c
left join "demo"."main"."stg_orders" o on c.customer_id = o.customer_id
group by c.customer_id, c.customer_name, c.email, c.created_at
  );
