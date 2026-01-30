
    
    

with all_values as (

    select
        budget_status as value_field,
        count(*) as n_records

    from "memory"."main"."fct_budget_performance"
    group by budget_status

)

select *
from all_values
where value_field not in (
    'over_budget','on_track','under_utilized','significantly_under'
)


