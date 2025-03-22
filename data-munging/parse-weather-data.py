import marimo

__generated_with = "0.11.25"
app = marimo.App(width="medium")


@app.cell
def _():
    return


@app.cell
def _():
    import marimo as mo
    import polars
    return mo, polars


@app.cell
def _(mo):
    raw_data = mo.sql(
        f"""


        SELECT * FROM './source_data/en_climate_daily_ON_6153193_*_P1D.csv' where "DATE/TIME" <= '2025-03-20'
        """
    )
    return (raw_data,)


@app.cell
def _(mo, raw_data):
    temperature_by_month = mo.sql(
        f"""
        SELECT date_trunc('month', "Date/Time") as month, mean("Mean Temp (°C)") as mean_temp_c FROM raw_data group by 1 order by month desc
        """
    )
    return (temperature_by_month,)


@app.cell
def _(temperature_by_month):
    temperature_by_month.write_csv('../sources/weather/temperature_by_month.csv')
    return


if __name__ == "__main__":
    app.run()
