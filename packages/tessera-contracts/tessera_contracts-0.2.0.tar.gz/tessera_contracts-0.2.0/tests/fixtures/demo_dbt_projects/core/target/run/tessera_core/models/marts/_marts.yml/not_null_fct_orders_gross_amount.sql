
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select gross_amount
from "memory"."main"."fct_orders"
where gross_amount is null



  
  
      
    ) dbt_internal_test