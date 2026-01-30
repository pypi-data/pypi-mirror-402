
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select conversion_id
from "memory"."main"."fct_conversions"
where conversion_id is null



  
  
      
    ) dbt_internal_test