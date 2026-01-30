
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select net_income
from "memory"."main"."fct_monthly_pl"
where net_income is null



  
  
      
    ) dbt_internal_test