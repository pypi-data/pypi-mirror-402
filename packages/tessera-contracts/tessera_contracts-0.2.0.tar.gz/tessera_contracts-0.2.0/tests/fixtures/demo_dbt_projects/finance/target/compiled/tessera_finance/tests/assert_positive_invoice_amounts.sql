-- Singular test: all invoices should have positive amounts
select
    invoice_id,
    amount
from "memory"."main"."fct_invoices"
where amount <= 0