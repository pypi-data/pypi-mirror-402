
    
    

with all_values as (

    select
        fiscal_quarter as value_field,
        count(*) as n_records

    from "memory"."main"."stg_budgets"
    group by fiscal_quarter

)

select *
from all_values
where value_field not in (
    'Q1','Q2','Q3','Q4'
)


