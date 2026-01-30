
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  -- Singular test: ensure no orders have future dates
select
    order_id,
    order_date
from "memory"."main"."fct_orders"
where order_date > current_date
  
  
      
    ) dbt_internal_test