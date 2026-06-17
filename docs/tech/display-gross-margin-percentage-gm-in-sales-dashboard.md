# Display Gross Margin Percentage (GM%) in Sales Dashboard
## Overview
This Business Requirements Document (BRD) outlines the need to enhance the Sales dashboard by adding a Gross Margin Percentage (GM%) metric. This addition will provide stakeholders with immediate visibility into profitability, complementing existing revenue and sales metrics.
## Description
The Sales dashboard currently displays key sales metrics such as revenue, units sold, and customer acquisition costs. To improve decision-making, the dashboard must include a clear and visible metric for Gross Margin Percentage (GM%). This metric will help stakeholders quickly assess profitability without requiring manual calculations or additional tools.
## Acceptance Criteria
- GM% is calculated and displayed accurately as (Revenue - COGS) / Revenue * 100.
- GM% is visible in the primary view of the Sales dashboard without requiring additional clicks or filters.
- GM% is formatted as a percentage with up to 2 decimal places for precision.
- The metric updates in real-time or near-real-time (e.g., daily) based on underlying sales and cost data.
- GM% is positioned in a logical section of the dashboard (e.g., near revenue or profit metrics).
- The dashboard remains performant (e.g., load time < 3 seconds) after adding GM%.
## Priority
High: This requirement is critical for providing stakeholders with a comprehensive view of sales performance and profitability.
## Implementation Notes
- How will the GM% metric be integrated into the existing dashboard layout?
- What are the potential performance implications of adding this new metric, and how will they be mitigated?