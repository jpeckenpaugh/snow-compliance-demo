-- ============================================================================
-- 04_risk_views.sql
-- Phase 3: transparent, rule-based contract-risk rubric. SIMULATED review.
-- Rules are data (ref_risk_rule) so the board can inspect and tune them.
-- ============================================================================

USE DATABASE SNOW_COMPLIANCE_DEMO;
USE SCHEMA CORE;

CREATE OR REPLACE TABLE CORE.ref_risk_rule (
  rule_id         STRING,
  clause_category STRING,
  signal          STRING,   -- PRESENT | ABSENT | KEYWORD
  pattern         STRING,   -- used when signal = KEYWORD
  points          INT,
  rationale       STRING
);

-- Category names are CUAD's ACTUAL 41 categories (verified in poc/analysis/cuad_shape_report.md).
-- Note: CUAD v1 has NO "Indemnification" or "Limitation of Liability" category; liability
-- exposure is expressed as "Uncapped Liability" / "Cap On Liability".
INSERT OVERWRITE INTO CORE.ref_risk_rule VALUES
  ('R1','Uncapped Liability','PRESENT', NULL, 40,'Uncapped liability exposure'),
  ('R2','Cap On Liability','ABSENT', NULL, 20,'No cap on liability'),
  ('R3','Termination For Convenience','PRESENT', NULL, 15,'Counterparty may exit at will'),
  ('R4','Anti-Assignment','PRESENT', NULL, 10,'Assignment restricted'),
  ('R5','Change Of Control','PRESENT', NULL, 10,'Change-of-control provision'),
  ('R6','Minimum Commitment','PRESENT', NULL, 10,'Minimum purchase/volume commitment'),
  ('R7','Governing Law','ABSENT', NULL, 10,'No governing law found'),
  ('R8','Non-Compete','PRESENT', NULL, 5,'Restrictive covenant present'),
  ('R9','Exclusivity','PRESENT', NULL, 5,'Exclusivity provision present');

-- --- Scoring view ------------------------------------------------------------
CREATE OR REPLACE VIEW MARTS.mart_matter_risk AS
SELECT m.matter_id,
       m.matter_name,
       c.contract_id,
       c.contract_type,
       SUM(
         CASE
           WHEN r.signal = 'ABSENT'  AND f.answer = 'No'  THEN r.points
           WHEN r.signal = 'PRESENT' AND f.answer = 'Yes' THEN r.points
           WHEN r.signal = 'KEYWORD' AND f.clause_text ILIKE '%' || r.pattern || '%' THEN r.points
           ELSE 0
         END
       ) AS risk_score
FROM CORE.dim_matter m
JOIN CORE.bridge_matter_contract b ON b.matter_id = m.matter_id
JOIN CORE.dim_contract c ON c.contract_id = b.contract_id
JOIN CORE.fact_clause f ON f.contract_id = c.contract_id
JOIN CORE.ref_risk_rule r ON r.clause_category = f.clause_category
GROUP BY 1,2,3,4;

-- --- Banded view -------------------------------------------------------------
CREATE OR REPLACE VIEW MARTS.mart_high_risk_register AS
SELECT matter_id, matter_name, contract_type, risk_score,
       CASE WHEN risk_score >= 60 THEN 'High'
            WHEN risk_score >= 30 THEN 'Medium'
            ELSE 'Low' END AS risk_band
FROM MARTS.mart_matter_risk;

-- --- Board-facing close-out query (run per attorney role) --------------------
-- SELECT matter_id, matter_name, contract_type, risk_score, risk_band
-- FROM MARTS.mart_high_risk_register
-- WHERE risk_band = 'High'
-- ORDER BY risk_score DESC;
