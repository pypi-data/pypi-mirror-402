
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

with all_values as (

    select
        account_type as value_field,
        count(*) as n_records

    from "memory"."main"."dim_accounts"
    group by account_type

)

select *
from all_values
where value_field not in (
    'revenue','expense','asset','liability','equity'
)



  
  
      
    ) dbt_internal_test