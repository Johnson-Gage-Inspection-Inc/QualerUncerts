import pandas as pd
from sqlalchemy import create_engine

engine = create_engine("postgresql://postgres:postgres@192.168.1.177:5432/qualer")


def write_csv_to_sql(engine, tableName, path):
    with open(path, encoding="utf-8") as f:
        pd.read_csv(f).to_sql(tableName, engine, if_exists="replace", index=False)


write_csv_to_sql(
    engine,
    "techniques",
    "C:/Users/JGI/Jeff H/Escape Dantes Inferno/QualerUncerts/csv/TechniquesList.csv",
)
write_csv_to_sql(
    engine,
    "service_capabilities",
    "C:/Users/JGI/Jeff H/Escape Dantes Inferno/QualerUncerts/csv/ServiceCapabilities.csv",
)

print("Done.")
