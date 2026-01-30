
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  -- Singular test: ensure all completed orders have positive revenue
-- This returns rows that FAIL the test

select
    order_id,
    revenue
from "demo"."main"."fct_orders"
where status = 'completed' and revenue <= 0
  
  
      
    ) dbt_internal_test