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

You'll note that in no month did we actually produce more than we consumed.
This is due to two factors:

1. Our system is a little undersized. Unfortunately we ran out of useable south
   facing roof space! Such is life.
2. We were continuously running an inefficient dehumidifier in the basement until
   August 2024 which was using a lot of power. Oops 🤦. I wrote about this [on mastodon](https://mastodon.social/@wlach/112869943948893579) last year.

With (2) fixed, I expect there will be some months in late spring/summer 2025 (May - August) where we are at least break-even.
