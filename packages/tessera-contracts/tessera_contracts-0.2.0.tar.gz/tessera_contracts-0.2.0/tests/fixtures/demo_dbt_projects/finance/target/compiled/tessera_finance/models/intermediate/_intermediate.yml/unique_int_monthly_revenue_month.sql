
    
    

select
    month as unique_field,
    count(*) as n_records

from "memory"."main"."int_monthly_revenue"
where month is not null
group by month
having count(*) > 1


