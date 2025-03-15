# Energy

There are two angles to energy use in a household: production and consumption.

## Consumption

With the addition of the heat pump added a significant amount of electrical load during the winter months.
You can see this clearly by looking at this chart of our monthly consumption:

```sql electricity_used_by_month
select Month,"Electric kWh","Utility Electric kWhr","Net kWh" from utility_measures.utility_measures
```

The above chart _discounts_ the effect of using solar.
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
The specifications on the heat pump suggested that the maximum

It's probably good to have for insurance purposes (e.g. if the heat pump breaks down) but I don't think it was necessary otherwise.

Now, let's look at how

## Production

To offset the increased energy use of the heat pump, we installed a 6kW solar system.
As mentioned, it's a 6kW system with a 5kW inverter.
Its peak output is _far_ more than what we would consume at any given time.

In Ontario, we use a system called "net metering", which allows you to resell excess
solar power at the retail rate that you buy it (not including the delivery charge,
which works out to a few cents per kWh).

We'll get more into the economics in the finance section,

The other variable here is of course self-consumption: by default, my solar system
will first try to power the house. What's left over at any given time is what's sold
to the grid. Under a tiered system, it's definitely better to use the power yourself
wherever possible: that way you avoid the delivery fee (a few cents per kWh).

There's a few ways we can get the quantities involved:

- We can get the kWhR values we send to the utility from our utility bill
- The SolarEdge inverter I have has telemetry values which tell you how much
  it produced over a given hour.
- By subtracting the two, we can get a rough idea of how much we used ourselves.

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
)
select
    sd.month as month,
    sd.total_generated_kWh as total_generated_kWh,
    ud.utility_measured_kwh as utility_measured_kwh,
    ud.utility_measured_kwhr as utility_measured_kwhr,
    sd.total_generated_kWh - ud.utility_measured_kwhr as self_consumption,
    ud.utility_measured_kwh - ud.utility_measured_kwhr as net_consumption
from solar_data sd
join utility_data ud
on sd.month = ud.month
order by sd.month
```

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
