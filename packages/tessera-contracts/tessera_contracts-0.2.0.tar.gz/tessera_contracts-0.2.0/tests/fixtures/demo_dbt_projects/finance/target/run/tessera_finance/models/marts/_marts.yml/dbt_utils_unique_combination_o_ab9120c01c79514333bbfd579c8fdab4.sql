
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  





with validation_errors as (

    select
        fiscal_period, department, category
    from "memory"."main"."fct_budget_performance"
    group by fiscal_period, department, category
    having count(*) > 1

)

select *
from validation_errors



  
  
      
    ) dbt_internal_test