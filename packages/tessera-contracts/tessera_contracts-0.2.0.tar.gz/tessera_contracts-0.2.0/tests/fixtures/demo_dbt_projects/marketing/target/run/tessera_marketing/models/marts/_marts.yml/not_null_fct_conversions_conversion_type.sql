
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select conversion_type
from "memory"."main"."fct_conversions"
where conversion_type is null



  
  
      
    ) dbt_internal_test