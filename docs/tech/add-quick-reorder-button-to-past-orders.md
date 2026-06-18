# Add Quick-Reorder Button to Past Orders
## Overview
This Business Requirements Document (BRD) outlines the implementation of a quick-reorder button for users to easily repurchase items from their past orders. The feature aims to enhance user experience by reducing the steps required to reorder items, thereby increasing customer satisfaction and retention.
## Description
The quick-reorder button will allow users to repurchase items from their past orders with a single click. When the button is clicked, all available items from the selected past order will be added to the user\'s cart. If any items are unavailable, the user will be notified, and those items will be excluded from the cart. This feature must be accessible on both desktop and mobile views and should only be available to logged-in users.
## Acceptance Criteria
- The quick-reorder button must be visible on the past orders page for each completed order.
- Clicking the quick-reorder button should add all items from the selected past order to the user\'s cart.
- If an item from the past order is no longer available, the user should be notified, and the unavailable item should be excluded from the cart.
- The cart should reflect the correct quantities and variants of the items from the past order.
- The user must be logged in to see and use the quick-reorder button.
- The quick-reorder functionality must work on both desktop and mobile views.
## Priority
High
## Implementation Notes
- How will the quick-reorder button be implemented on the past orders page?
- How will the system handle cases where an item is no longer available?
- How will the system ensure that the cart reflects the correct quantities and variants of the items from the past order?