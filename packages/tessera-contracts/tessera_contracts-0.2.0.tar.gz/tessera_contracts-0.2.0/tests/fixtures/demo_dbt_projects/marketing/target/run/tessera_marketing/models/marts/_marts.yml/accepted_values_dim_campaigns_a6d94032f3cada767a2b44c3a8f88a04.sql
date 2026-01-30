
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

with all_values as (

    select
        performance_tier as value_field,
        count(*) as n_records

    from "memory"."main"."dim_campaigns"
    group by performance_tier

)

select *
from all_values
where value_field not in (
    'high_performer','break_even','underperformer'
)



  
  
      
    ) dbt_internal_test