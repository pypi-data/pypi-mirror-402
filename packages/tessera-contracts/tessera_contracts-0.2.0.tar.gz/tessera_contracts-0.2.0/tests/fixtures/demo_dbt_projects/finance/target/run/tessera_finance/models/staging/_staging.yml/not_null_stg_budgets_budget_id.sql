
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select budget_id
from "memory"."main"."stg_budgets"
where budget_id is null



  
  
      
    ) dbt_internal_test