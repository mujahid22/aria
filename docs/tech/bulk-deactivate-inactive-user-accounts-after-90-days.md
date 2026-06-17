# Bulk Deactivate Inactive User Accounts After 90 Days
## Overview
This Business Requirements Document (BRD) outlines the need for a bulk deactivation feature for user accounts that have been inactive for 90 days or more. This feature aims to enhance system security and resource management by automating the identification and deactivation of inactive accounts.
## Description
The system shall enable administrators to bulk-deactivate user accounts that have been inactive for 90 days or more. Inactivity is defined as no login or system activity within the specified period. This feature will streamline account management, reduce security risks, and ensure compliance with organizational policies.
## Acceptance Criteria
- Admins can access a dashboard or tool to identify users inactive for 90+ days.
- The system provides a bulk selection option for admins to choose inactive users for deactivation.
- Admins receive a confirmation prompt before finalizing bulk deactivation.
- The system logs all bulk deactivation actions for audit purposes.
- Deactivated users cannot log in or access the system post-deactivation.
- Admins can export a report of deactivated users with details (e.g., username, last activity date).
## Priority
High
## Implementation Notes
- How will the system handle users who are inactive but have active sessions?
- What is the process for reactivating a deactivated user account?