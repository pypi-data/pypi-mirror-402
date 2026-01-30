
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

with all_values as (

    select
        conversion_type as value_field,
        count(*) as n_records

    from "memory"."main"."stg_conversions"
    group by conversion_type

)

select *
from all_values
where value_field not in (
    'purchase','signup','demo_request','download'
)



  
  
      
    ) dbt_internal_test