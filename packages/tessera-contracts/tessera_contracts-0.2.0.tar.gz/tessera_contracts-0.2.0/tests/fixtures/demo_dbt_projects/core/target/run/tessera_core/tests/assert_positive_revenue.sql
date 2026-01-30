
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  -- Singular test: ensure no negative revenue
select
    order_id,
    gross_amount
from "memory"."main"."fct_orders"
where gross_amount < 0
  
  
      
    ) dbt_internal_test