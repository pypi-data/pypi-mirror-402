
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

with all_values as (

    select
        engagement_level as value_field,
        count(*) as n_records

    from "memory"."main"."fct_web_traffic"
    group by engagement_level

)

select *
from all_values
where value_field not in (
    'engaged','browsing','bounce'
)



  
  
      
    ) dbt_internal_test