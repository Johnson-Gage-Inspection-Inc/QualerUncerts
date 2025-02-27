import pandas as pd
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:postgres@192.168.1.177:5432/qualer')


def import_uncertainty_budgets(engine):
    path = 'C:/Users/JGI/Jeff H/Escape Dantes Inferno/QualerUncerts/csv/AllUncertaintyBudgets.csv'
    with open(path, encoding='utf-8') as f:
        df = pd.read_csv(f)

    df.to_sql('uncertainty_budgets', engine, if_exists='replace', index=False)

# Remove duplicates (UncertaintyBudgetId must be unique)
    with engine.connect() as conn:
        conn.execute(text('DELETE FROM uncertainty_budgets a USING uncertainty_budgets b WHERE a.ctid < b.ctid AND a."UncertaintyBudgetId" = b."UncertaintyBudgetId";'))

# Set FK for SiteId ref sites.SiteId
    with engine.connect() as conn:
        conn.execute(text('ALTER TABLE uncertainty_budgets ADD CONSTRAINT "FK_uncertainty_budgets_SiteId" FOREIGN KEY ("SiteId") REFERENCES sites ("siteid");'))


def main(engine, import_uncertainty_budgets):
    import_uncertainty_budgets(engine)

    print("Done.")


if __name__ == "__main__":
    main(engine, import_uncertainty_budgets)
