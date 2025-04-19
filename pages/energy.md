---
sidebar_position: 3
---

# Energy

There are two angles to energy use in a household: production and consumption.

## Consumption

With the addition of the heat pump added a significant amount of electrical load during the winter months.
You can see this clearly by looking at this chart of our monthly consumption:

```sql total_production_consumption_export
with utility_data as (
    select
        Month as month,
        "Electric kWh" as utility_measured_kwh,
        "Utility Electric kWhr" as utility_measured_kwhr
    from utility_measures.utility_measures
),
solar_data as (
    select
        date_trunc('month', cast(time as date)) as month,
        sum(kWh) as total_generated_kWh
    from utility_measures.solar_output
    group by month
),
all_months as (
    select distinct month from utility_data
    union
    select distinct month from solar_data
)
select
    am.month as month,
    coalesce(sd.total_generated_kWh, 0) as total_generated_kWh,
    ud.utility_measured_kwh as utility_measured_kwh,
    ud.utility_measured_kwhr as utility_measured_kwhr,
    coalesce(sd.total_generated_kWh, 0) - ud.utility_measured_kwhr as self_consumption,
    ud.utility_measured_kwh + self_consumption as total_consumption,
    ud.utility_measured_kwh - ud.utility_measured_kwhr as net_consumption
from all_months am
left join solar_data sd on am.month = sd.month
left join utility_data ud on am.month = ud.month
where am.month <= '2024-09-01'
order by am.month
```

<LineChart 
    data={total_production_consumption_export}
    x=month
    y=total_consumption
    yFmt="kWh"
    >
<ReferenceLine x="2023-10-01" label="Heat Pump Installed" hideValue=true />
</LineChart>

The above chart includes both energy drawn from the grid _and_ self-consumption from our solar system.
For more information on that calculation, see the next section.

The system comes with a 10kW backup strip, but honestly we probably didn't use it much (if at all) based on the data I'm seeing.
Unfortunately we aren't measuring regular consumption patterns but one day in January 2024 I got
curious, went outside, and periodically checked the meter:

```sql meter_readings
with readings as (
    select
        reading,
        timestamp
    from (
        values
        (74104, '2024-01-15 09:24'),
        (74108, '2024-01-15 12:46'),
        (74126, '2024-01-15 21:00')
    ) as t(reading, timestamp)
)
select
    reading,
    timestamp
from readings
```

<DataTable data={meter_readings}>
    <Column id="timestamp" title="Time" />
    <Column id="reading" title="Reading" fmt=id />
</DataTable>

That works out to an average of about 1.91 kWh _per hour_ on a very cold day.
Between 9:24 and 12:46 (when the weather was coldest), we used only about 4 kWh.
The specifications on the heat pump suggest that the maximum output of the heat pump itself is 3kW, leading me to suspect that we just didn't need the electric backup.
It's probably good to have for insurance purposes (e.g. if the heat pump breaks down) but I don't think it was necessary otherwise.

## Production

To offset the increased energy use of the heat pump, we installed a 6kW solar system.
As mentioned, it's a 6kW system with a 5kW inverter.
Its peak output is _far_ more than what we would consume at any given time.

In Ontario, we use a system called "net metering", which allows you to resell excess
solar power at the retail rate that you buy it (not including the delivery charge,
which works out to a few cents per kWh).

We'll get more into the economics in the finance section, but the birds eye view of a system like this is that it produces _a lot more_ in the summer than in the winter.
If you're trying to fully offset your electricity use over a full year (not a possibility in our
case) you'd size so as to produce enough in the summer to offset your winter.

The other variable here is of course self-consumption: by default, my solar system
will first try to power the house. What's left over at any given time is what's sold
to the grid. The utility only measures the latter, of course, what we use ourselves is only
visible to us.

To get a handle on these variables, I sourced information from two different sources:

- We can get the kWhR values we send to the utility from our utility bill
- The SolarEdge inverter I have has telemetry values which tell you how much
  it produced over a given hour.

By subtracting the second from the first, we can get a rough idea of how much we used ourselves.

<DataTable data={total_production_consumption_export}>
    <Column id="month" title="Month" />
    <Column id="total_generated_kWh" title="Total solar production (kWh)" />
    <Column id="utility_measured_kwh" title="Total electricity consumption (kWh)" />
    <Column id="utility_measured_kwhr" title="Electricity sent to grid (kWh)" />
</DataTable>

You can watch as our net consumption (total produced subtracted from total produced)
goes down over the course of the year as the days get longer and our need for heating goes down:

<LineChart 
    data={total_production_consumption_export}
    x=month
    y=net_consumption
    yFmt="kWh" />

It's also interesting to look at "self consumption" on its own.
This is electricity directly consumed by our household, without being sent to the grid.

<LineChart 
    data={total_production_consumption_export}
    x=month
    y=self_consumption
    yFmt="kWh" />

You'll note that only in September 2024 did we actually produce more than we consumed.
This is due to two factors:

1. Our system is a little undersized. Unfortunately we ran out of useable south
   facing roof space! Such is life.
2. We were continuously running an inefficient dehumidifier in the basement until August 2024 which was using a lot of power. Oops 🤦. I wrote about this [on mastodon](https://mastodon.social/@wlach/112869943948893579) last year.

### Solar irradiance

Since the system runs by converting sunlight into electricity, the main factor
influencing how much it produces is how much sunlight hits the panels.
Obviously, this will vary a bit year over year.
We can use the NASA [POWER](https://power.larc.nasa.gov/) data to get a handle on what the values were for 2024, and then present the counterfactual of what they might have been for other years (where we had different amounts of solar irradiance).

#### Deriving an "irradiance" ratio

The NASA POWER data provides a total amount of insolation (in kWh/m^2/day) for a given location.
We can compare this to the system's _actual_ production to get an idea of how these two values relate.

```sql solar_irradiance_to_production_ratio
with solar_output as (
    select
        date_trunc('day', cast(time as date)) as day,
        sum(kWh) as total_generated_kWh
    from utility_measures.solar_output
    group by day
),
irradiance_data as (
    select
        Date as day,
        sum("Irradiance (kWh/m^2/day)") as total_irradiance
    from weather.irradiance
    group by day
)
select
    solar_output.day as day,
    solar_output.total_generated_kWh as total_generated_kWh,
    irradiance_data.total_irradiance as total_irradiance,
    total_generated_kWh / total_irradiance as ratio
    from solar_output left join irradiance_data on solar_output.day = irradiance_data.day where solar_output.day >= '2024-01-01' and solar_output.day <= '2024-12-31'
```

<LineChart 
    data={solar_irradiance_to_production_ratio}
    x=day
    y=ratio
    />

As you can see, the ratio gets pretty messy (especially in the winter when there are other factors like snow cover at play), but overall things balance out.
The mean value over this series was 4.7633.
Multiplying this by the total irradiance value for year gives us an estimated value of 6343.67, pretty close to our actual generation figure of 6557.73.

#### Estimating production for previous years

To estimate the production for previous years, we can take the average of the ratio and multiply it by the total irradiance value for that year.

```sql estimated_solar_production_by_year
select
    date_trunc('year', irradiance.Date) as year,
    sum("Irradiance (kWh/m^2/day)") as total_irradiance,
    4.7633 * total_irradiance as estimated_production
from weather.irradiance group by year
```

<BarChart
data={estimated_solar_production_by_year}
x=year
y=estimated_production
xFmt="YYYY"
yFmt="kWh"
/>

As you can see, there are notable differences between years.

```sql average_solar_production_by_year
with yearly_estimated_production as (
    select
        date_trunc('year', irradiance.Date) as year,
        sum("Irradiance (kWh/m^2/day)") as total_irradiance,
        4.76 * total_irradiance as estimated_production
    from weather.irradiance group by year
)
select
min(estimated_production) as minimum_estimated_production,
max(estimated_production) as maximum_estimated_production,
avg(estimated_production) as average_estimated_production
from yearly_estimated_production
```

Breaking that out into averages, we get <Value 
    data={average_solar_production_by_year}
    column=minimum_estimated_production 
    row=0
/> kWh as a minimum, <Value 
    data={average_solar_production_by_year}
    column=maximum_estimated_production 
    row=0 /> kWh as a maximum, and <Value
    data={average_solar_production_by_year}
    column=average_estimated_production
    row=0
    /> kWh (or about 100 kWh below our estimated generation of 6557 kWh for 2024) as an average.

#### Conclusion

Irradiance can make a difference, but not an enormous one.
We have sunny and cloudy days in Ontario, but averaged over a year, the end result is pretty similar.
The results we got in 2024 are probably pretty close to what we'll get in subsequent years (subject to panel degradation, of course).
