
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  





with validation_errors as (

    select
        month, category, subcategory
    from "memory"."main"."int_expense_by_category"
    group by month, category, subcategory
    having count(*) > 1

)

select *
from validation_errors



  
  
      
    ) dbt_internal_test