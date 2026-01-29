"""Debug script to test TUI rendering."""

from jortt_report.tui import TimesheetApp

if __name__ == "__main__":
    print("Starting TUI debug test...")
    app = TimesheetApp()

    # Test data loading
    df = app.get_timesheet_data()
    print(f"Loaded {len(df)} rows from database")

    if len(df) > 0:
        week, year = app.get_target_week()
        print(f"Target week: {week}, year: {year}")

        import polars as pl
        filtered = df.filter(
            (pl.col("time_registration_date").dt.week() == week)
            & (pl.col("time_registration_date").dt.year() == year)
        )
        print(f"Filtered {len(filtered)} rows for current week")

        if len(filtered) > 0:
            print("\nSample data for current week:")
            print(filtered.select(["customer", "project_name", "time_registration_date", "time_registration_quantity"]).head(5))

    print("\nLaunching TUI...")
    app.run()
