
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select fiscal_quarter
from "memory"."main"."stg_budgets"
where fiscal_quarter is null



  
  
      
    ) dbt_internal_test