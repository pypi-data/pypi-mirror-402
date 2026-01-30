
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select expense_id
from "memory"."main"."fct_expenses"
where expense_id is null



  
  
      
    ) dbt_internal_test