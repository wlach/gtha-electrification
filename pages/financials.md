# Financials

## Utility Bills

```sql total_cost
select cast(Month as date) as month, "Total electricity bill" as total, 'electricity' as bill_type from utility_measures.utility_measures
union all
select cast(Month as date) as month, "Total gas bill" as total, 'gas' as bill_type from utility_measures.utility_measures
order by month asc
```

I think the most intuitive way of looking at the financial impact is to just look at utility bills, month over month. What do they add up to?
From this, we can get an intuition on the effect of our actions.

For the purposes of this site, I'm going to directly compare the period between September 2022 and August 2023 (the year before the work was done) with the period between September 2023 and August 2024 (the year after the work was done). There's obviously reasons why these periods aren't necessarily _directly_ comparable (e.g. weather) but you have to start somewhere, right?

Let's start just by looking at a graph of what things look like month over month:

<AreaChart 
    data={total_cost}
    x=month
    y=total
    yFmt="cad"
    series=bill_type
/>

Just glancing at it, you can see that our overall energy costs have gone **up** in
January over the previous year, despite the fact that we've added solar panels and
insulation. However, you can't really measure the effect of a change like this looking
at just one month: the more meaningful comparison is over a whole year:

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
One further caveat is that our solar system was only installed in mid-November 2023, so these numbers don't reflect the savings that I'd expect if we had the system installed in a full year. In particular, September and October are usually good solar months.

I also included some bonus calculations for a few counterfactuals:

1. The "no gas" row is just me subtracting out the gas bill from the 2023-2024 period.
   As mentioned in the [narrative](./electrification-and-solar) section: we're only using gas for the dryer
   (and very little at that), so the expense is almost entirely fixed charges which we could have avoided if we were a little more aggressive about buying new appliances.
1. Since a solar system doesn't make sense for everyone, I thought it might be useful to look at costs with no solar system installed. For these calculations, I estimated we would have had to purchase all the solar energy we generated from the utility at approximately $0.12 per kWh (this is a conservative estimate that accounts for both the electricity rate and delivery charges we would have paid).

But, I think discounting that, there are two takeaways:

1. On a pure cost basis, a heat pump with electric backup is going to be more expensive than a natural gas furnace given current commodity prices. The difference isn't huge (and arguably worth it given the environmental benefits), but it is there.
2. An appropriately-sized solar system can help defray these costs, assuming it's good value for the money.

And by doing so, we can find out some interesting things about time of use rates and how they totally change the economics of a system like this. Let's dig in.

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

TODO: Insert some kind of chart or graphic showing how this works

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

## Time to break-even

Given the earlier comments about the cost of a solar system, you might be wondering if the investment makes sense.

The way to determine this is to project the numbers we got above over time.

<Slider
    title="Yearly percent increase" 
    name=yearly_percent_increase
    defaultValue=5
    min=0
    max=10
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

<BarChart 
    data={total_value_over_a_year}
    x=year
    y=cumulative_savings
/>

Assumptions:

1. The Ontario government continues to allow net metering under the current terms.
2. The system doesn't require repairs or maintenance.

TODO: Needs more narrative, thoughts about expected increases (without getting too political), maybe a note that 2024 was a bad solar year. Perhaps create a model that assumes a constant rate over the year?
