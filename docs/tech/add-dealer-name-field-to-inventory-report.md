# Add Dealer Name Field to Inventory Report
## Overview
This Business Requirements Document (BRD) outlines the need to extend the Inventory report functionality by adding a Dealer name field. This enhancement will improve traceability and clarity in inventory management by associating each inventory item with its respective dealer.
## Description
The current Inventory report system does not include a field for capturing the Dealer name associated with inventory items. This limitation reduces the report’s usefulness for tracking and auditing purposes. The proposed feature will:
- Add a Dealer name field to the Inventory report input form.
- Ensure the Dealer name is saved and associated with the inventory item in the database.
- Display the Dealer name in the Inventory report output.
- Support alphanumeric characters and common punctuation in the Dealer name field.
- Include the Dealer name in report exports (e.g., PDF/CSV).
- Allow editing of the Dealer name when updating an inventory item.
## Acceptance Criteria
- The Inventory report input form includes a field to enter the Dealer name.
- The Dealer name is saved and associated with the inventory item.
- The Dealer name is displayed in the Inventory report output.
- The Dealer name field supports alphanumeric characters and common punctuation.
- The Dealer name is included in the report export (e.g., PDF/CSV) if applicable.
- Editing an inventory item allows updating the Dealer name.
## Priority
High
## Implementation Notes
- How will the Dealer name field be validated to ensure it only contains alphanumeric characters and common punctuation?
- What is the expected behavior when a user attempts to edit an inventory item without a Dealer name associated with it?
