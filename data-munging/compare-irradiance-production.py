import marimo

__generated_with = "0.11.25"
app = marimo.App(width="medium")


@app.cell
def _():
    import polars as pl
    return (pl,)


@app.cell
def _(pl):
    def get_irradiance(year):
        irradiance = pl.read_csv(f'nasa_power_irradiance_{year}.csv')
        return irradiance.with_columns(pl.col("Date").str.slice(0, 10).str.strptime(pl.Date, "%Y-%m-%d").alias("Date"))
    irradiance = get_irradiance('2024')
    irradiance
    return get_irradiance, irradiance


@app.cell
def _(pl):
    inverter_output = pl.read_csv('../sources/utility_measures/solar_output.csv')
    inverter_output = inverter_output.filter(pl.col("time") >=  pl.lit("2024-01-01"))
    inverter_output = inverter_output.with_columns(
        pl.col("time").str.strptime(pl.Datetime, "%Y-%m-%d %H:%M:%S").alias("time")
    )
    daily_generation_2024 = inverter_output.group_by(pl.col("time").dt.date().alias("Date")).agg(pl.sum("kWh").alias("Daily_Generation"))
    daily_generation_2024
    return daily_generation_2024, inverter_output


@app.cell
def _(daily_generation_2024, irradiance, pl):
    irradiance_vs_daily_generation = daily_generation_2024.join(irradiance, "Date")

    irradiance_vs_daily_generation = irradiance_vs_daily_generation.with_columns(
        (pl.col("Daily_Generation") / pl.col("Irradiance (kWh/m^2/day)"))
        .alias("Generation_to_Irradiance_Ratio")
    )

    irradiance_vs_daily_generation
    return (irradiance_vs_daily_generation,)


@app.cell
def _(irradiance_vs_daily_generation):
    import marimo as mo
    import matplotlib.pyplot as plt

    # Assuming your merged DataFrame is called merged_df
    # And your date column is 'Date' and ratio column is 'Generation_to_Irradiance_Ratio'

    dates = irradiance_vs_daily_generation["Date"].to_numpy()
    ratios = irradiance_vs_daily_generation["Generation_to_Irradiance_Ratio"].to_numpy()

    fig, ax = plt.subplots(figsize=(12, 6))  # Adjust figure size as needed
    ax.plot(dates, ratios)

    ax.set_xlabel("Date")
    ax.set_ylabel("Generation / Irradiance Ratio")
    ax.set_title("Daily Generation to Irradiance Ratio Over Time")
    ax.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.show()
    return ax, dates, fig, mo, plt, ratios


@app.cell
def _(irradiance_vs_daily_generation):
    mean_generation_to_irradiance_ratio = irradiance_vs_daily_generation["Generation_to_Irradiance_Ratio"].mean()
    irradiance_sum_2024 = irradiance_vs_daily_generation["Irradiance (kWh/m^2/day)"].sum()
    estimated_generation_based_on_irradiance = irradiance_sum_2024 * mean_generation_to_irradiance_ratio
    actual_generation = irradiance_vs_daily_generation["Daily_Generation"].sum()

    return (
        actual_generation,
        estimated_generation_based_on_irradiance,
        irradiance_sum_2024,
        mean_generation_to_irradiance_ratio,
    )


@app.cell
def _(
    actual_generation,
    estimated_generation_based_on_irradiance,
    irradiance_sum_2024,
    mean_generation_to_irradiance_ratio,
    mo,
):
    mo.md(f"""
        ## Generation sum

        By taking the sum of generation and multiplying it by a ratio, we can get a sum for other years. This will tell us whether the estimate is accurate:

        ESTIMATED_IRRADIANCE = MEAN_GENERATION_TO_IRRADIANCE_RATIO * TOTAL_IRRADIANCE<br/>
        ESTIMATED_IRRADIANCE = {mean_generation_to_irradiance_ratio} * {irradiance_sum_2024}<br/>
        ACTUAL_IRRADIANCE = ACTUAL_DAILY_GENERATION_SUM

        Plugging actual numbers into that we get an estimated value of {estimated_generation_based_on_irradiance} for irradiance compared with an actual value of {actual_generation}. Pretty close!
        """
    )
    return


@app.cell
def _():


    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
