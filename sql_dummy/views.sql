create or replace view mtab_sample_intensity as

select a.exp_id as exp_id, a.id as mtab_id, a.mz, a.rt, a."withMS2" as withms2, s.id as sample_id, i.intensity, s.control
from metabolite a, intensity i, sample s
where

-- join clauses
a.id = i.mtab_id
and s.id = i.sample_id

order by mtab_id, sample_id;