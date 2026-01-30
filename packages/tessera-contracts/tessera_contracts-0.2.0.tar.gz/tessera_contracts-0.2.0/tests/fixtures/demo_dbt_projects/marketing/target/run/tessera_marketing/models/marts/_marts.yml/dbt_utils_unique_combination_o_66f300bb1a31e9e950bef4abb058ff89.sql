
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  





with validation_errors as (

    select
        date, channel
    from "memory"."main"."fct_marketing_daily"
    group by date, channel
    having count(*) > 1

)

select *
from validation_errors



  
  
      
    ) dbt_internal_test