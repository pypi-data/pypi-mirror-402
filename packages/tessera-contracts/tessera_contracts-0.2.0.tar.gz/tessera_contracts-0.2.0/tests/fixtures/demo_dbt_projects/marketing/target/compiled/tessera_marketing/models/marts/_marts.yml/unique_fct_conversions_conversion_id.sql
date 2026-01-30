
    
    

select
    conversion_id as unique_field,
    count(*) as n_records

from "memory"."main"."fct_conversions"
where conversion_id is not null
group by conversion_id
having count(*) > 1


