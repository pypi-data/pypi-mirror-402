
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select month
from "memory"."main"."fct_monthly_pl"
where month is null



  
  
      
    ) dbt_internal_test