





with validation_errors as (

    select
        fiscal_period, department, category
    from "memory"."main"."fct_budget_performance"
    group by fiscal_period, department, category
    having count(*) > 1

)

select *
from validation_errors


