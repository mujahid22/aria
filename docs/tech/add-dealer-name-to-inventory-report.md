# Add Dealer Name to Inventory Report
## Overview
This Business Requirements Document (BRD) outlines the need to extend the Inventory report functionality to include the Dealer name for each inventory item. This enhancement will improve traceability and accountability by associating inventory items with their respective dealers.
## Description
The current Inventory report does not include the Dealer name associated with each inventory item. This requirement aims to extend the Inventory report to allow users to add, store, and display the Dealer name for each item. This will ensure better tracking and reporting capabilities.
## Acceptance Criteria
- The Inventory report form includes a field to input the Dealer name.
- The Dealer name is saved and associated with the inventory item in the database.
- The Dealer name is displayed in the Inventory report for each item.
- The Dealer name field supports alphanumeric characters and is limited to 100 characters.
- Editing an existing inventory item allows updating the Dealer name.
- The Dealer name is visible in both the detailed and summary views of the Inventory report.
## Priority
High
## Implementation Notes
- How will the Dealer name be validated to ensure it is within the 100 character limit?
- How will the Dealer name be displayed in the Inventory report, and what will be the format of the report?