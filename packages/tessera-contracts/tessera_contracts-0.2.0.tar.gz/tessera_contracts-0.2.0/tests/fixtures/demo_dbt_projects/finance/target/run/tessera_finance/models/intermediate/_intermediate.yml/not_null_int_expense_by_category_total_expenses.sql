
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select total_expenses
from "memory"."main"."int_expense_by_category"
where total_expenses is null



  
  
      
    ) dbt_internal_test