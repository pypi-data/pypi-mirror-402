
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select budgeted_amount
from "memory"."main"."fct_budget_performance"
where budgeted_amount is null



  
  
      
    ) dbt_internal_test