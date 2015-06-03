--query 12, 13
with sq1 as (
select exp_id, mtab_id, mz, rt, withms2, a.sample_id, intensity, control,
  (select value from sample_attr b where a.sample_id=b.sample_id and name='media') as attr_media
from mtab_sample_intensity a
where

-- mz/rt clause
abs(a.rt - 100) <= 30
and abs(1e6 * (113 - a.mz) / a.mz) <= 0.5

), sq2 as (
select mtab_id, control, attr_media, avg(intensity) as avg_intensity from sq1
group by mtab_id, control, attr_media
), sq3 as (
select exp_id, sq1.mtab_id, mz, rt, withms2, sample_id, intensity, sq1.control, sq1.attr_media
, (select avg_intensity from sq2
   where sq1.mtab_id=sq2.mtab_id
   and sq1.attr_media=sq2.attr_media
   and sq2.control=1) as iic
from sq1
)
select * from sq3 where intensity > 10 * iic
order by mtab_id, attr_media, sample_id, control, iic