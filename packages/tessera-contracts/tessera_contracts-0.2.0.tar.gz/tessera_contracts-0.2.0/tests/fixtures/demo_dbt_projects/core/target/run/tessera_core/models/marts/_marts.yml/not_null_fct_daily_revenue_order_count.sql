
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select order_count
from "memory"."main"."fct_daily_revenue"
where order_count is null



  
  
      
    ) dbt_internal_test