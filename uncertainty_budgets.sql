-- Step 1: Backup the original table
CREATE TABLE uncertainty_budgets_backup AS
SELECT * FROM uncertainty_budgets;

-- Step 2: Create a temporary table to store the data during migration
CREATE TEMP TABLE temp_uncertainty_budgets AS
SELECT * FROM uncertainty_budgets;

-- Step 3: Drop and recreate uncertainty_budgets (removing ServiceGroupId and TechniqueId)
DROP TABLE uncertainty_budgets CASCADE;

CREATE TABLE uncertainty_budgets (
    "UncertaintyBudgetId" BIGINT PRIMARY KEY,
    "BudgetName" TEXT NOT NULL,
    "ComponentsCount" BIGINT NOT NULL,
    "ActivationDate" TEXT NOT NULL,
    "ExpirationDate" TEXT NOT NULL,
    "SiteId" BIGINT NOT NULL,
    FOREIGN KEY ("SiteId") REFERENCES sites("siteid") NOT VALID
);

-- Step 5: Update existing records in `sites`
UPDATE sites s
SET "SiteName" = t."SiteName",
    "IsMismatchedSite" = t."IsMismatchedSite"
FROM temp_uncertainty_budgets t
WHERE s.siteid = t."SiteId";

-- Step 6: Insert unique service groups (since service_groups is new)
INSERT INTO service_groups ("ServiceGroupId")
SELECT DISTINCT "ServiceGroupId" FROM temp_uncertainty_budgets
ON CONFLICT DO NOTHING;

-- Step 8: Insert unique uncertainty budgets
INSERT INTO uncertainty_budgets (
    "UncertaintyBudgetId", "BudgetName", "ComponentsCount", "ActivationDate", "ExpirationDate", "SiteId"
)
SELECT DISTINCT
    "UncertaintyBudgetId", "BudgetName", "ComponentsCount", "ActivationDate", "ExpirationDate", "SiteId"
FROM temp_uncertainty_budgets;

-- Step 9: Create Join Tables
CREATE TABLE uncertainty_budget_service_groups (
    "UncertaintyBudgetId" BIGINT NOT NULL,
    "ServiceGroupId" BIGINT NOT NULL,
    PRIMARY KEY ("UncertaintyBudgetId", "ServiceGroupId"),
    FOREIGN KEY ("UncertaintyBudgetId") REFERENCES uncertainty_budgets("UncertaintyBudgetId") NOT VALID,
    FOREIGN KEY ("ServiceGroupId") REFERENCES service_groups("ServiceGroupId") NOT VALID
);

CREATE TABLE uncertainty_budget_techniques (
    "UncertaintyBudgetId" BIGINT NOT NULL,
    "TechniqueId" BIGINT NOT NULL,
    PRIMARY KEY ("UncertaintyBudgetId", "TechniqueId"),
    FOREIGN KEY ("UncertaintyBudgetId") REFERENCES uncertainty_budgets("UncertaintyBudgetId") NOT VALID,
    FOREIGN KEY ("TechniqueId") REFERENCES techniques("TechniqueId") NOT VALID
);

-- Step 10: Populate Join Tables
INSERT INTO uncertainty_budget_service_groups ("UncertaintyBudgetId", "ServiceGroupId")
SELECT DISTINCT "UncertaintyBudgetId", "ServiceGroupId" FROM temp_uncertainty_budgets
ON CONFLICT DO NOTHING;

INSERT INTO uncertainty_budget_techniques ("UncertaintyBudgetId", "TechniqueId")
SELECT DISTINCT "UncertaintyBudgetId", "TechniqueId" FROM temp_uncertainty_budgets
ON CONFLICT DO NOTHING;

-- Step 12: Drop the temporary table
DROP TABLE temp_uncertainty_budgets;
