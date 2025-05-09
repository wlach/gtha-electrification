---
sidebar_position: 4
---

# Environmental Impact

<Alert status="warning">
The below analysis doesn't really attempt to model marginal emissions. See
the last section for another perspective added later.
</Alert>

A primary reason we embarked on this project was environmental reasons, so let's go into some detail there. In general, using energy causes CO₂ emissions. For the purposes of this analysis, I'm going to use figures provided by the [Government of Canada](https://www.canada.ca/en/environment-climate-change/services/climate-change/pricing-pollution-how-it-will-work/output-based-pricing-system/federal-greenhouse-gas-offset-system/emission-factors-reference-values.html) which gives the following figures for Ontario, year-over-year:

```sql gov_estimates_co2
select g.year, g.co2_g as gas_m3, e.co2_g as electric_kwh from
(select year,co2_g from co2_measures.gov_estimates where unit='m3_gas') g
join (select year,co2_g from co2_measures.gov_estimates where unit='kwh_electricity') e on g.year=e.year
```

<DataTable data={gov_estimates_co2}>
    <Column id="year" title="Year" />
    <Column id="gas_m3" title="Grams per m3 gas" />
    <Column id="electric_kwh" title="Grams per grid kWh" />
</DataTable>

You might find the values for electricity above shockingly low: I certainly did initially. There's a few reasons for this:

1. This isn't an apples to apples comparison. An m3 of natural gas embodies something on the order of ~11kWh. Mentally you probably want to put a zero at the end of the kWh figures to even start comparing them.
2. Ontario's grid is relatively low carbon: a mixture of nuclear, hydro, wind and natural gas (with nuclear and hydroelectricity dominating). Over the last few years, the use of gas has gone up somewhat, which explains the year-over-year increases.

In any case, let's plug in the numbers and see what we get for 2022-09-01 - 2022-08-31 (the year before this project) and 2023-09-01 - 2024-08-31 (after this project was implemented):

```sql total_carbon_emissions
with net_electricity as (
    select
        case
            when Month >= '2022-09-01' and Month < '2023-09-01' then '2022-2023'
            when Month >= '2023-09-01' and Month < '2024-09-01' then '2023-2024'
        end as year,
        sum("Electric kWh") as total_electric_kwh,
        sum("Utility Electric kWhr") as total_electric_kwhr,
        sum("Electric kWh") - sum("Utility Electric kWhr") as net_electric_kwh,
        sum("Gas m3") as total_gas_m3
    from utility_measures.utility_measures
    where Month >= '2022-09-01' and Month < '2024-09-01'
    group by year
),
co2_calculations as (
    select
        year,
        total_gas_m3,
        net_electric_kwh,
        total_gas_m3 * (select co2_g from co2_measures.gov_estimates where year = extract(year from current_date) and unit = 'm3_gas') / 1000000 as gas_co2_tons,
        net_electric_kwh * (select co2_g from co2_measures.gov_estimates where year = extract(year from current_date) and unit = 'kwh_electricity') / 1000000 as electric_co2_tons
    from net_electricity
)
select
    year,
    total_gas_m3,
    net_electric_kwh,
    gas_co2_tons,
    electric_co2_tons,
    gas_co2_tons + electric_co2_tons as total_co2_tons
from co2_calculations
order by year
```

<DataTable data={total_carbon_emissions}>
    <Column id="year" title="Year" />
    <Column id="total_gas_m3" title="Total Gas (m3)" />
    <Column id="net_electric_kwh" title="Grid Electricity (kWh)" />
    <Column id="gas_co2_tons" title="Gas CO2 Tons" />
    <Column id="electric_co2_tons" title="Electricity CO2 Tons" />
    <Column id="total_co2_tons" title="Total CO2 Tons" />
</DataTable>

"Net electricity" represents the actual amount of electricity we pulled in from the grid, and is what we used to calculate our carbon emissions.
Note that we did not have solar installed for the full period of comparison (we only got it mid-November 2023, 2.5 months after the evaluation period started): I would expect that our net marginal carbon emissions to go _down_ for the next year (2024-2025).

Probably unsurprisingly, gas dominates the CO₂ emissions in 2022-2023. Not just because it's vastly more emitting, but also because a good portion of the house's energy use came from it! After the heat pump and hot water heater installation, all of that heat gets converted to being generated via electricity, which we generate via either our solar system (zero marginal emissions) or the grid (negligible marginal emissions, as discussed above).

## Emissions by month

You can see this more clearly if you graph out our CO₂ emissions by month:

```sql co2_by_month
select Month as month, ("Gas m3" * (select co2_g from co2_measures.gov_estimates where year = extract(year from Month) and unit = 'm3_gas') + "Electric kWh" * (select co2_g from co2_measures.gov_estimates where year = extract(year from Month) and unit = 'kwh_electricity')) / 1000000 as co2_tons
from utility_measures.utility_measures
```

<LineChart 
    data={co2_by_month}
    x=month
    y=co2_tons
    yFmt="LT" />

The spikes in CO2 usage from heating in the winter months are completely gone.
There is a minor benefit from switching the stove and hot water heating to electric, but that's almost just noise.

## Embodied emissions

An obvious question is what are the embodied emissions of the heat pump, solar panels, etc. that we installed?
This is obviously difficult to calculate but [credible sources](https://www.sciencedirect.com/science/article/pii/S0378778817323101) online suggest a few tons each.
Which is to say, that after just a year or two we'll have recouped the carbon costs of producing the heat pump.
The case for solar panels is on the surface a little less compelling given those figures, but bear in mind that it's often displacing a natural gas plant at the margins so it's probably greater than you might initially expect (edit: see last section for some notes on that).

## Human-scale impact

Ok, so we're saving about 3 tons of CO₂ a year with this thing.
What does that even mean?
I think it's useful to look at some points of comparison.
These are just some random things I found on the Internet using Google (so take them with many grains of salt), but I think they're useful as a point of comparison:

```sql emissions_comparison
select
    description,
    emissions
from (
    values
    ('<a href="https://co2.myclimate.org/en/portfolios?calculation_id=7816314">Round-trip flight between Toronto, Canada (YYZ) and Delhi, India (DEL)</a>',
     '5.1'),
    ('<a href="https://www.ethicalconsumer.org/food-drink/climate-impact-meat-vegetarian-vegan-diets">Vegetarian diet for one year</a>',
     '1.39'),
    ('<a href="https://www.ethicalconsumer.org/food-drink/climate-impact-meat-vegetarian-vegan-diets">Regular meat eating diet for one year</a>',
     '2'),
    ('<a href="https://co2.myclimate.org/en/portfolios?calculation_id=7816318">Driving commute of 10080km (20km/day, 252 working days) in a regular car</a>',
     '3.5')
) as t(description, emissions)
```

<DataTable data={emissions_comparison}> 
    <Column id="description" contentType="html" title="Description" /> 
    <Column id="emissions" title="CO₂ emissions (tons)" /> 
</DataTable>

As a further point of reference, [the suggested global limit for per-capita personal emissions is 2.1 tons](https://www.oxfam.org/en/press-releases/richest-1-burn-through-their-entire-annual-carbon-limit-just-10-days).
It's very likely our activities still cause me to exceed that (such is the western lifestyle), but at least we're removing some element of harm.

## Epilogue: Marginal emissions

Shortly after writing the first version of this analysis, I shared it with an Energy Markets Manager at my current employer ([Voltus](https://voltus.co)), who suggested I also consider some research done by the [Toronto Atmospheric Fund] (TAF).
I didn't revisit the full model to account for it, but I thought it was worth adding a brief epilogue to reflect their findings.

The above analysis assumed a (mostly) static world: one where there is a fixed emission factor associated with the electricity produced by the grid to satisfy demand, and a fixed emission factor to be offset by the energy produced by the solar panels (which has zero marginal emissions).
But we know that's not the case: the electricity consumed by the heat pump needs to be satisfied by _something_ (particularly in the winter).
And likewise, the electricity produced by the solar panels (and put onto the grid) offsets power at the margins, which (in Ontario at least) is often produced by a natural gas power plant and has considerably higher emissions than the average amount used above.

TAF has attempted to quantify these factors in [Ontario Electricity Emissions Factors and Guidelines].
Their numbers suggest that the emissions per kWh are actually _3 to 5 times higher_ than the Government of Canada estimates above at the margins.
This changes the picture in both good and bad ways for this project.

The bad news is that this increases the apparent emissions impact of the heat pump more than average-based estimates would suggest.
It's still going to be better than natural gas: partly because it generates multiple kWh of heat per unit of energy, and partly because not all marginal electricity use is from natural gas plants.

The good news is that this makes the solar system look a lot better, since it's _displacing_ those marginal emissions! Let's take a look at its output from that
perspective for 2024:

```sql marginal_co2_by_month
select date_trunc('month', cast(time as date)) as month, sum(kWh * gco2_kwh)/1000.0/1000.0 as co2_tons_averted, 'CO₂ Averted' as label from utility_measures.solar_output
left join co2_measures.taf_estimates on (
    solar_output.tou_period=taf_estimates.tou_period and
    solar_output.period=taf_estimates.period
) where time > '2024-01-01'
group by 1
```

<LineChart 
    data={marginal_co2_by_month}
    x=month
    y=co2_tons_averted
    series=label
    yFmt="LT" />

In sum, about a ton of extra CO₂ averted every year by using solar power to displace natural gas generation.
For various reasons (increases in demand, nuclear refurbishment), this number is expected to rise significantly over the next 6 years. By TAF's estimates, I'd expect the amount displaced to reach 2 tons in 2030.

[Toronto Atmospheric Fund]: https://taf.ca/
[Ontario Electricity Emissions Factors and Guidelines]: https://taf.ca/publications/ontario-electricity-emissions-factors-2024/
