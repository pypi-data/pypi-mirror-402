
    
    

with all_values as (

    select
        category as value_field,
        count(*) as n_records

    from "memory"."main"."stg_expenses"
    group by category

)

select *
from all_values
where value_field not in (
    'marketing','operations','hr','sales','admin'
)


