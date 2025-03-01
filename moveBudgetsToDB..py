import pandas as pd
from sqlalchemy import create_engine

engine = create_engine("postgresql://postgres:postgres@192.168.1.177:5432/qualer")


def import_uncertainty_budgets(engine):
    import_dataframe_to_sql(
        engine,
        "uncertainty_components",
        "C:/Users/JGI/Jeff H/Escape Dantes Inferno/QualerUncerts/csv/UncertaintyComponents.csv",
    )
    import_dataframe_to_sql(
        engine,
        "uncertainty_values",
        "C:/Users/JGI/Jeff H/Escape Dantes Inferno/QualerUncerts/csv/UncertaintyValues.csv",
    )


def import_dataframe_to_sql(engine, table, path):
    with open(path, encoding="utf-8") as f:
        df = pd.read_csv(f)

    df.to_sql(table, engine, if_exists="replace", index=False)


def main(engine, import_uncertainty_budgets):
    import_uncertainty_budgets(engine)

    print("Done.")


if __name__ == "__main__":
    main(engine, import_uncertainty_budgets)
