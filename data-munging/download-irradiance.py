import marimo

__generated_with = "0.11.25"
app = marimo.App(width="medium")


@app.cell
def _():
    import altair as alt
    return (alt,)


@app.cell
def _():
    import requests
    import polars as pl
    from io import StringIO

    def download_nasa_power_irradiance(latitude, longitude, year):
        start_date = f"{year}0101"
        end_date = f"{year}1231"

        url = (
            f"https://power.larc.nasa.gov/api/temporal/daily/point?parameters=ALLSKY_SFC_SW_DWN&community=RE&longitude={longitude}&latitude={latitude}&start={start_date}&end={end_date}&format=CSV"
        )

        response = requests.get(url)
        data_start = response.text.find("YEAR,MO,DY,ALLSKY_SFC_SW_DWN")
        csv_data = response.text[data_start:]
        df = pl.read_csv(StringIO(csv_data))

        df = df.rename({
            "YEAR": "Year",
            "MO": "Month",
            "DY": "Day",
            "ALLSKY_SFC_SW_DWN": "Irradiance (kWh/m^2/day)"
        })

        df = df.with_columns(pl.datetime(pl.col("Year"), pl.col("Month"), pl.col("Day")).alias("Date"))
        df = df.select(["Date", "Irradiance (kWh/m^2/day)"])

        return df

    latitude = 43.256687
    longitude=-79.8690589
    years = range(2015, 2020)

    all_data = []
    for year in years:
        irradiance_data = download_nasa_power_irradiance(latitude, longitude, year)
        irradiance_data.write_csv(f"nasa_power_irradiance_{year}.csv")
        all_data.append(irradiance_data)
    irradiance_data = pl.concat(all_data)
    irradiance_data
    return (
        StringIO,
        all_data,
        download_nasa_power_irradiance,
        irradiance_data,
        latitude,
        longitude,
        pl,
        requests,
        year,
        years,
    )


@app.cell
def _(mo):
    yearly_total_irradiance = mo.sql(
        f"""
        select date_trunc('year', "Date") as year, sum("Irradiance (kWh/m^2/day)") as yearly_irradiance from "./nasa_power*.csv" group by 1 order by 1 desc
        """
    )
    return (yearly_total_irradiance,)


@app.cell
def _(mo, yearly_total_irradiance):
    _df = mo.sql(
        f"""
        select avg(yearly_irradiance) from yearly_total_irradiance
        """
    )
    return


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _(irradiance_data, mo):
    _df = mo.sql(
        f"""
        SELECT * FROM irradiance_data
        """
    )
    return


@app.cell
def _(mo):
    solar_output_by_day = mo.sql(
        f"""
        SELECT date_trunc('day', time) as Date, sum(kWh) as kWh FROM '../sources/utility_measures/solar_output.csv' group by 1 order by 1 desc
        """
    )
    return (solar_output_by_day,)


@app.cell
def _(alt, irradiance_data, mo, solar_output_by_day):
    chart = alt.Chart(irradiance_data).mark_bar().encode(
        x='Date', # Encoding along the x-axis
        y='Irradiance (kWh/m^2/day)', # Encoding along the y-axis
    )

    # Make it reactive ⚡
    chart = mo.ui.altair_chart(chart)

    output_chart = alt.Chart(solar_output_by_day).mark_bar().encode(
        x='Date', # Encoding along the x-axis
        y='kWh', # Encoding along the y-axis
    )
    output_chart = mo.ui.altair_chart(output_chart)

    return chart, output_chart


@app.cell
def _(chart, mo, output_chart):
    mo.vstack([chart, chart.value.head(), output_chart])
    return


if __name__ == "__main__":
    app.run()
