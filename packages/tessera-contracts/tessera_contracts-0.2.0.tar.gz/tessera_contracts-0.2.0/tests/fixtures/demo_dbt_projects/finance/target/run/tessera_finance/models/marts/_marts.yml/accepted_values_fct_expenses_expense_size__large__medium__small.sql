
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

with all_values as (

    select
        expense_size as value_field,
        count(*) as n_records

    from "memory"."main"."fct_expenses"
    group by expense_size

)

select *
from all_values
where value_field not in (
    'large','medium','small'
)



  
  
      
    ) dbt_internal_test