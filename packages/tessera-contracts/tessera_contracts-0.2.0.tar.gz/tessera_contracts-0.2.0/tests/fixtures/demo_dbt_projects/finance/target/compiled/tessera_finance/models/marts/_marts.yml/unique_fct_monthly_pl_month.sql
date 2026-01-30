
    
    

select
    month as unique_field,
    count(*) as n_records

from "memory"."main"."fct_monthly_pl"
where month is not null
group by month
having count(*) > 1


