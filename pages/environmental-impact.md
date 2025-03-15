# Environmental Impact

The main reason we embarked on this project was environmental reasons, so let's go into some detail there. In general, using energy causes CO2 emissions. For the purposes of this analysis, I'm going to use figures provided by the [Government of Canada](https://www.canada.ca/en/environment-climate-change/services/climate-change/pricing-pollution-how-it-will-work/output-based-pricing-system/federal-greenhouse-gas-offset-system/emission-factors-reference-values.html) which gives the following figures for Ontario, year-over-year:

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

1. This isn't an apples to apples comparison. An m3 of natural gas embodies something on the order of ~11kWh. Mentally you probably want to put a zero at the end of the kWh figures to compare them 1:1 (obviously they are not the same thing).
2. Ontario's grid is relatively low carbon: a mixture of nuclear, hydro, wind and natural gas (with nuclear and hydroelectricity dominating). Over the last few years, the use of gas has gone up somewhat, which explains the year-over-year increases.

In any case, let's plug in the numbers and see what we get for 2022-09-01 - 2022-08-31 (the year before this project) and 2023-09-01 - 2024-08-31 (after this project was implemented):

```sql total_carbon_emissions
select
    case
        when Month >= '2022-09-01' and Month < '2023-09-01' then '2022-2023'
        when Month >= '2023-09-01' and Month < '2024-09-01' then '2023-2024'
    end as year,
    sum("Gas m3") as total_gas_m3,
    sum("Electric kWh") as total_electric_kwh,
    sum("Net kWh") as net_electric_kwh,
    sum("Gas m3" * (select co2_g from co2_measures.gov_estimates where year = extract(year from Month) and unit = 'm3_gas')) / 1000000 as gas_co2_tons,
    sum("Net kWh" * (select co2_g from co2_measures.gov_estimates where year = extract(year from Month) and unit = 'kwh_electricity')) / 1000000 as electric_co2_tons,
    (sum("Gas m3" * (select co2_g from co2_measures.gov_estimates where year = extract(year from Month) and unit = 'm3_gas')) + sum("Electric kWh" * (select co2_g from co2_measures.gov_estimates where year = extract(year from Month) and unit = 'kwh_electricity'))) / 1000000 as total_co2_tons
from utility_measures.utility_measures
where Month >= '2022-09-01' and Month < '2024-09-01'
group by year
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

"Total Electricity" represents the total electricity consumed by the household, and represents the
counterfactual of "how much would we need if we hadn't installed solar"?
"Net electricity" represents the actual amount of electricity we pulled in from the grid, and is what we used to calculate our carbon emissions.
Note that we did not have solar installed for the full period of comparison (we only got it mid-November 2023, 2.5 months after the evaluation period started): I would expect that our net marginal carbon emissions to go _down_ for the next year (2024-2025).

Probably unsurprisingly, gas dominates the CO2 emissions in 2022-2023. Not just because it's vastly more emitting, but also because a good portion of the house's energy use comes from it! After the heat pump and hot water heater installation, all of that heat gets converted to being generated via electricity, which we generate via either our solar system (zero marginal emissions) or the grid (negligible marginal emissions, as discussed above).

You can see this more clearly if you graph out our CO2 emissions by month:

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
The case for solar panels is on the surface a little less compelling given those figures, but bear in mind that it's often displacing a natural gas plant at the margins so it's probably greater than you might think. I'm not

## Human-scale impact

Ok, so we're saving about 3 tons of CO2 a year with this thing.
What does that even mean?
I think it's useful to look at some points of comparison.
These are just some random things I found on the Internet using Google (take them with many grains of salt), but I think they're useful as a point of comparison:

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
    <Column id="emissions" title="CO2 Emissions (tons)" /> 
</DataTable>

As a further point of reference, [the suggested global limit for per-capita personal emissions is 2.1 tons](https://www.oxfam.org/en/press-releases/richest-1-burn-through-their-entire-annual-carbon-limit-just-10-days).
It's very likely my activities still cause me to exceed that (such is the western lifestyle), but at least we're removing some element of harm.
