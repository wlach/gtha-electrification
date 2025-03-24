---
sidebar_position: 5
---

# Financials

## Utility Bills

```sql total_cost
select cast(Month as date) as month, "Total electricity bill" as total, 'electricity' as bill_type from utility_measures.utility_measures
union all
select cast(Month as date) as month, "Total gas bill" as total, 'gas' as bill_type from utility_measures.utility_measures
order by month asc
```

```sql temperature_by_month
select tbm.month,mean_temp_c from weather.temperature_by_month tbm
join (${total_cost}) tc on tc.month = tbm.month
group by 1, 2
order by tbm.month
```

I think the most intuitive way of looking at the financial impact is to just look at utility bills, month over month. What do they add up to?
From this, we can get an idea on the effect of our actions.

For the purposes of this site, I'm going to directly compare the period between September 2022 and August 2023 (the year before the work was done) with the period between September 2023 and August 2024 (the year after the work was done).
There's obvious reasons why these periods aren't _directly_ comparable but you have to start somewhere, right?

Let's graph that out:

<AreaChart
data={total_cost}
x=month
y=total
yFmt="cad"
series=bill_type
title="Utility Bills (total)"
connectGroup=total_bill_cost>
<ReferenceLine x="2023-10-01" label="Heat Pump" hideValue=true />
<ReferenceLine x="2023-11-01" label="Solar Panels" hideValue=true />
</AreaChart>

<LineChart
    data={temperature_by_month}
    x=month
    y=mean_temp_c
    title="Monthly Mean Temperature"
    yFmt='#,##0.00"°C"'
    connectGroup=total_bill_cost
/>

Just glancing at it, you can see that our overall energy costs have gone **up** in January over the previous year, despite the fact that we've added solar panels and insulation.
Part of this is just due to the fact that January was just a colder month in 2024 than it was in 2023, but it does illustrate the general point that a heat pump is not going to be a panacea: it may be efficient, but it still costs money to run!

That aside, I think it's a bit of mistake to compare this change over such a short period.
The more meaningful comparison is over a whole year.

```sql total_cost_year
with base_year as (
    select '2022-2023' as period,
           sum("Total electricity bill") + sum("Total gas bill") as total
    from utility_measures.utility_measures
    where Month >= '2022-09-01' and Month <= '2023-08-31'
),
solar_value as (
    select '2023-2024 (no solar credit)' as period,
           sum("Total electricity bill") + sum("Total gas bill") +
           (select sum(kWh) * 0.13 from utility_measures.solar_output) as total
    from utility_measures.utility_measures
    where Month >= '2023-09-01' and Month <= '2024-08-31'
),
solar_value_no_gas as (
    select '2023-2024 (no solar credit, no gas)' as period,
           sum("Total electricity bill") +
           (select sum(kWh) * 0.13 from utility_measures.solar_output) as total
    from utility_measures.utility_measures
    where Month >= '2023-09-01' and Month <= '2024-08-31'
)
select period, total,
       (select total from base_year) - total as savings
from (
    select '2022-2023' as period,
           sum("Total electricity bill") + sum("Total gas bill") as total
    from utility_measures.utility_measures
    where Month >= '2022-09-01' and Month <= '2023-08-31'
    union all
    select '2023-2024' as period,
           sum("Total electricity bill") + sum("Total gas bill") as total
    from utility_measures.utility_measures
    where Month >= '2023-09-01' and Month <= '2024-08-31'
    union all
    select '2023-2024 (no gas)' as period,
           sum("Total electricity bill") as total
    from utility_measures.utility_measures
    where Month >= '2023-09-01' and Month <= '2024-08-31'
    union all
    select * from solar_value
    union all
    select * from solar_value_no_gas
) as combined
order by period asc
```

<DataTable data={total_cost_year}>
    <Column id="period" title="Period" />
    <Column id="total" title="Total cost" fmt=cad />
    <Column id="savings" title="Savings (cost) vs 2022-2023" fmt=cad />
</DataTable>

The first two rows represent actual, real numbers.
Unfortunately my utility bills don't go any further back than September 2022, so I can't really do an apples-to-apples comparison of the "total utility bill cost".

I also included some bonus calculations for a few counterfactuals:

1. The "no gas" row is just me subtracting out the gas bill from the 2023-2024 period.
   As mentioned in the [narrative](./electrification-and-solar) section: we're only using gas for the dryer
   (and very little at that), so the expense is almost entirely fixed charges which we could have avoided if we were a little more aggressive about buying new appliances.
1. Since a solar system doesn't make sense for everyone, I thought it might be useful to look at costs with no solar system installed. For these calculations, I estimated we would have had to purchase all the solar energy we generated from the utility at approximately $0.12 per kWh (this is a conservative estimate that accounts for both the electricity rate and delivery charges we would have paid).

I really do want to emphasize that this isn't an apples-to-apples comparison.
There are just so many reasons why the numbers are the way they are:

1. Our solar system was only installed in mid-November 2023, so these numbers don't reflect the savings that I'd expect if we had the system installed in a full year. In particular, September and October are usually good solar months.
1. As mentioned on the energy page, we had an inefficient dehumidifier running in the basement which somewhat distorted our energy use.
1. I'm pretty sure we used air conditioning more in 2024, especially in June/July/August. Central air conditioning is nice, what can I say?
1. Shifting commodity and energy prices year over year.
1. The [Canadian Carbon Tax](https://en.wikipedia.org/wiki/Carbon_pricing_in_Canada) (which was offset by a rebate in Ontario, not incorporated into these numbers).
1. Weather differences.

Even discounting all of that, I feel there's still a pretty overall picture here that I don't expect to change:

1. On a pure cost basis, a heat pump with electric backup is going to be more expensive than a natural gas furnace given current commodity prices. The difference isn't huge (and arguably worth it given the environmental benefits), but it is there.
1. An appropriately-sized solar system can help defray these costs, assuming it's good value for the money.

On the second point, let's look more closely at the solar system and its economics.

## Solar

The above tells a story of how, so long as natural gas remains relatively cheap and electricity expensive by comparison, heating a house with the former is going to win out economically.
I thought it would be useful to break out the solar system by itself, although note that this system wouldn't have really made sense for us pre-heat-pump (when our electricity usage would have been less than the total output of the solar system) since net metering has no provision to credit you for over-production.

### Net Metering

At the time we installed the solar system, you could **only** use this program in conjunction with
the tiered rate plan, which gives a fixed rate for the first block of electricity (600 in the summer, 1000 in the winter)
and a higher rate for the second block (see the next section for time-of-use billing, and how it's a bit of a game changer).
This makes it pretty easy to calculate the value of your solar installation, assuming
your production is less than or equal to your consumption, just measure the net production per month and then apply the tiered rate to it.
Electricity that you produce and use yourself (self-consumption) has a somewhat higher value, since you avoid the distribution fee (a few cents per kWh).

<!--
TODO: Insert some kind of chart or graphic showing how this works
-->

### Time of use billing: game changer?

In January 2024, it became possible for someone with a net metering contract (i.e. us) to switch from the tiered billing rate to time of use, both for _consumption_ and _production_.
The idea behind time-of-use is simple: charge people more during periods of peak demand (when more expensive dispatchable energy is likely to be in use) than non-peak.

Having the intuition that it would be better (since solar production corresponds to at least mid-peak), I asked my utility company to switch over.
It wasn't until I ran the numbers that I realized _how much better_ though.

Let's look at an arbitrary sunny day in September 2024:

```sql sunny_day_september_2024
select strftime(time, '%H:00') as hour, kWh, tou_rate, (kWh * tou_rate) as tou_value, tiered_rate, (kWh * tiered_rate) as tiered_value, tou_value / tiered_value as pct_improvement from
utility_measures.solar_output where time >= '2024-09-03 00:00:00' and time < '2024-09-04 00:00:00' and kWh > 0
```

<DataTable data={sunny_day_september_2024} totalRow=true rows=all>
    <Column id="hour" title="Hour" />
    <Column id="kWh" title="Solar Production (kWh)" />
    <Column id="tou_value" title="Time of Use Value" fmt=cad />
    <Column id="tiered_value" title="Tiered Value" fmt=cad />
    <Column id="pct_improvement" title="Percent Improvement" fmt=pct totalAgg="mean" />
</DataTable>

Huge difference! Let's look at how that adds up over a year:

```sql monthly_tiered_vs_tou
with values as (
    select
        strftime(time, '%Y-%m') as month,
        sum(kWh) as kWh,
        sum(kWh * tou_rate) as tou_value,
        sum(kWh * tiered_rate) as tiered_value
    from utility_measures.solar_output
    group by month
)
select
    month,
    kWh,
    tou_value,
    tiered_value,
    (tou_value - tiered_value) / ((tou_value + tiered_value) / 2) as pct_improvement
from values
```

<DataTable data={monthly_tiered_vs_tou} totalRow={true} rows=all>
    <Column id=month title="Month" />
    <Column id="kWh" title="Solar Production (kWh)" />
    <Column id="tou_value" title="Time of Use Value" fmt=cad />
    <Column id="tiered_value" title="Tiered Value" fmt=cad />
    <Column id="pct_improvement" title="Percent Improvement" fmt=pct totalAgg="mean" />
</DataTable>

~$120 for doing nothing more than sending an email to switch a rate plan. Not bad!

### Time to break-even

Details aside, the fundamental question I really wanted to answer was: does this investment make sense?
To try to answer it, I tried to project the numbers I got above for the net metering solution over the next 19 years:

<Slider
    title="Yearly percent increase" 
    name=yearly_percent_increase
    defaultValue=2
    min=0
    max=5
    step=1
/>

```sql total_value_over_a_year
with recursive yearly_values as (
    select
        1 as year,
        sum(kWh) as kWh_value,
        sum(kWh * tou_rate) as tou_value,
        sum(kWh * tou_rate) as cumulative_savings
    from utility_measures.solar_output
    where time >= '2024-01' and time <= '2024-12'
    union all
    select
        year + 1,
        kWh_value,
        tou_value * (1 + CAST('${inputs.yearly_percent_increase}' AS FLOAT) / 100),
        cumulative_savings + (tou_value * (1 + CAST('${inputs.yearly_percent_increase}' AS FLOAT) / 100))
    from yearly_values
    where year < 20
)
select
    year,
    kWh_value,
    tou_value,
    cumulative_savings
from yearly_values
```

<BarChart data={total_value_over_a_year} x=year y=cumulative_savings yMax={30000}>
<ReferenceLine y=20000 label="Rough break even" />
</BarChart>

You can adjust the slider above to see how the model performs under different scenarios.
I opted for a very conservative average 2% yearly increase over time.
If I had to guess, my suspicion is that it will be more than that, but I'm not entirely sure how much.
Energy prices in Ontario have historically been a hot potato and my guess is that political pressure will keep increases in check.

As usual, there are some caveats:

1. There's some amount of variation in solar insolation year over year (usually on the order of a few percentage points). From my preliminary research, 2024 was a slightly below average year for Ontario.
1. It doesn't account for the value of self-consumption. This saves you a few cents of distribution cost per kWh.
1. [Consumer electricity prices actually _decreased_ slightly at the end of 2024](https://www.oeb.ca/consumer-information-and-protection/electricity-rates/historical-electricity-rates), so the estimates for the 2nd year might be high all other things being equal. I assumed that eventual rate increases would make this moot.

It also goes without saying there's a few assumptions going into this model:

1. The Ontario government continues to allow net metering under the current terms.
1. The system doesn't require repairs or maintenance outside of the warranty, which would also cost money.

Limitations aside, I think the overall picture holds: this isn't a great business case and illustrates the challenges of residential solar in Ontario.
